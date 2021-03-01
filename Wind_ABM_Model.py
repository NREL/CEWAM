# -*- coding:utf-8 -*-
"""
Created on December 31 2020

@author Julien Walzberg - Julien.Walzberg@nrel.gov

Model - Circular Economy Wind Agent-based Model (CEWAM)
This module contains the model class that creates and activates agents. The
module also defines inputs (default values can be changed by user) and collect
outputs.
"""


# TODO: Next steps - continue HERE
#  1) Continue with other agents - follow memo (including agent order)
#    ii) manufacturer
#      * TPB decision to manufacture thermoplastic blades
#      * Manufacturing waste
#      * Unittests
#    iii) landfill
#      * Capacity assessment
#      * Unittests
#    iv) regulator
#      * Regulation enactment depending on landfill capacity
#      * Unittests
#  2) More unittests:
#    i) for recycler and other agents similar to recycler write
#    unittests to check initial distribution of types
#    ii) also try to build unittests to check that outputs are correct
#    ("mini extreme scenario" to test that the model output intermediate
#    variables (like adoption of pathways and such correctly)
#  3) Use a machine learning metamodel to calibrate the ABM quicker
#  4) A reinforcement learning could be used in the future (long term)
#  5) Avoid calling the scheduler unless there are no other choices
#  6) lifetime extension: use doi:10.1088/1757-899X/429/1/012024 to write about
#  green procurement
#  7) (Optional) Improving code:
#    i) The "initial_dic_from_key_list" function could be replaced by:
#    a = dict.fromkeys(a, 0)

from mesa import Model
from Wind_ABM_WindPlantOwner import WindPlantOwner
from Wind_ABM_Manufacturer import Manufacturer
from Wind_ABM_Developer import Developer
from Wind_ABM_Recycler import Recycler
from Wind_ABM_Landfill import Landfill
from Wind_ABM_Regulator import Regulator
from mesa.time import RandomActivation
from mesa.time import BaseScheduler
from mesa.space import NetworkGrid
from mesa.datacollection import DataCollector
import networkx as nx
import numpy as np
from math import *
import pandas as pd
import random
import scipy
import warnings
from scipy.stats import truncnorm
import copy


class WindABM(Model):
    def __init__(self,
                 seed=None,
                 manufacturers={
                     "wind_blade": 7, "plastics_n_boards": 100, "cement": 97},
                 developers={'lifetime_extension': 10},
                 recyclers={
                     "dissolution": 7, "pyrolysis": 2,
                     "mechanical_recycling": 3, "cement_co_processing": 1},
                 landfills={"landfill": 47},
                 small_world_networks={
                     "wind_plant_owners": {
                         "node_degree": 15, "rewiring_prob": 0.1},
                     "developers": {"node_degree": 5, "rewiring_prob": 0.1},
                     "recyclers": {"node_degree": 5, "rewiring_prob": 0.1},
                     "manufacturers": {"node_degree": 15,
                                       "rewiring_prob": 0.1},
                     "landfills": {"node_degree": 5, "rewiring_prob": 0.1},
                     "regulators": {"node_degree": 5, "rewiring_prob": 0.1}},
                 external_files={
                     "state_distances": "StatesAdjacencyMatrix.csv", "uswtdb":
                     "uswtdb_v3_3_20210114.csv"},
                 # TODO: growth rates from 95-by-35.Adv and
                 #  95-by-35+Elec.Adv+DR scenarios in: C:\Users\jwalzber\
                 #  Documents\Winter21\Wind_ABM\Modeling\Data\ProjectedCapacity
                 growth_rates={
                     'Alabama': 0.39, 'Arizona': 0.09, 'Arkansas': 0.47,
                     'California': 0.05, 'Colorado': 0.02, 'Connecticut': 0.24,
                     'Delaware': 0.25, 'Florida': 0.22, 'Georgia': 0.41,
                     'Idaho': 0.04, 'Illinois': 0.06, 'Indiana': 0.04,
                     'Iowa': 0.03, 'Kansas': 0.01, 'Kentucky': 0.45,
                     'Louisiana': 0.39, 'Maine': 0.02, 'Maryland': 0.12,
                     'Massachusetts': 0.15, 'Michigan': 0.08,
                     'Minnesota': 0.01, 'Mississippi': 0.2, 'Missouri': 0.09,
                     'Montana': 0.05, 'Nebraska': 0.04, 'Nevada': 0.1,
                     'New Hampshire': 0.06, 'New Jersey': 0.23,
                     'New Mexico': 0.07, 'New York': 0.08,
                     'North Carolina': 0.16, 'North Dakota': 0.01,
                     'Ohio': 0.1, 'Oklahoma': 0.02, 'Oregon': 0.03,
                     'Pennsylvania': 0.09, 'Rhode Island': 0.09,
                     'South Carolina': 0.44, 'South Dakota': 0.04,
                     'Tennessee': 0.18, 'Texas': 0.03, 'Utah': 0.03,
                     'Vermont': 0.06, 'Virginia': 0.14, 'Washington': 0.05,
                     'West Virginia': 0.06, 'Wisconsin': 0.11,
                     'Wyoming': 0.03},
                 average_lifetime=20.0,
                 weibull_shape_factor=2.2,
                 blade_size_to_mass_model={'coefficient': 0.0026,
                                           'power': 2.1447},
                 cap_to_diameter_model={'coefficient': 57,
                                        'power': 0.44},
                 temporal_scope={
                     'pre_simulation': 2000, 'simulation_start': 2020,
                     'simulation_end': 2051},
                 blades_per_rotor=3,
                 # TODO
                 eol_pathways={
                     "lifetime_extension": True, "dissolution": True,
                     "pyrolysis": True, "mechanical_recycling": True,
                     "cement_co_processing": True, "landfill": True},
                 eol_pathways_dist_init={
                     "lifetime_extension": 0.005, "dissolution": 0.0,
                     "pyrolysis": 0.005, "mechanical_recycling": 0.005,
                     "cement_co_processing": 0.005, "landfill": 0.98},
                 tpb_eol_coeff={'w_bi': 0.33, 'w_a': 0.30, 'w_sn': 0.56,
                                'w_pbc': -0.13, 'w_p': 0.11, 'w_b': -0.21},
                 attitude_eol_parameters={
                     'mean': 0.5, 'standard_deviation': 0.1, 'min': 0,
                     'max': 1},
                 # TODO: complete dic with circular choices from other
                 #  decision than eol (e.g., conventional vs thermoplastic
                 #  blades)
                 choices_circularity={
                     "lifetime_extension": True, "dissolution": False,
                     "pyrolysis": True, "mechanical_recycling": True,
                     "cement_co_processing": True, "landfill": False,
                     "thermoset": False, "thermoplastic": True},
                 # TODO: all $/blade need to be converted into $/tons based
                 #  on agents characteristics OR even better: use $/ton
                 #  directly
                 decommissioning_cost=[1300, 33000],
                 # TODO: find values for dissolution recycling process
                 lifetime_extension_costs=[600, 6000],
                 rec_processes_costs={
                     "dissolution": [0, 1E-6], "pyrolysis": [280.5, 550],
                     "mechanical_recycling": [212.3, 286],
                     "cement_co_processing": [0, 1E-6]},
                 landfill_costs={
                     'Alabama': 33.41, 'Arizona': 43.39, 'Arkansas': 40.23,
                     'California': 55.56, 'Colorado': 62.04, 'Delaware': 85.00,
                     'Florida': 55.08, 'Georgia': 48.77, 'Idaho': 68.71,
                     'Illinois': 51.78, 'Indiana': 47.91, 'Iowa': 48.47,
                     'Kansas': 39.32, 'Kentucky': 29.82, 'Louisiana': 33.28,
                     'Maine': 78.50, 'Maryland': 68.57, 'Massachusetts': 77.00,
                     'Michigan': 41.97, 'Minnesota': 63.52,
                     'Mississippi': 38.70, 'Missouri': 62.42, 'Montana': 49.36,
                     'Nebraska': 39.21, 'Nevada': 74.20,
                     'New Hampshire': 74.34, 'New Jersey': 81.91,
                     'New Mexico': 38.28, 'New York': 68.40,
                     'North Carolina': 43.87, 'North Dakota': 46.98,
                     'Ohio': 44.35, 'Oklahoma': 50.22, 'Oregon': 71.28,
                     'Pennsylvania': 68.07, 'Rhode Island': 110.00,
                     'South Carolina': 44.03, 'South Dakota': 49.14,
                     'Tennessee': 50.24, 'Texas': 40.18, 'Utah': 32.08,
                     'Vermont': 66.53, 'Virginia': 52.22, 'Washington': 89.08,
                     'West Virginia': 51.50, 'Wisconsin': 65.00,
                     'Wyoming': 74.45},
                 transport_shreds={'shredding_costs': [99, 132],
                                   'transport_cost_shreds': [0.0314, 0.0820]},
                 transport_segments={
                     'cutting_costs': 27.56, 'transport_cost_segments': 8.7,
                     'length_segment': 30, 'segment_per_truck': 2},
                 transport_repair=1.57,
                 eol_pathways_transport_mode={
                     "lifetime_extension": 'transport_repair',
                     "dissolution": 'undefined', "pyrolysis": 'undefined',
                     "mechanical_recycling": 'undefined',
                     "cement_co_processing": 'transport_segments',
                     "landfill": 'undefined'},
                 # TODO: find values for dissolution recycling process
                 lifetime_extension_revenues=[124, 1.7E6],
                 rec_processes_revenues={
                     "dissolution": [0, 1E-6], "pyrolysis": [660, 1320],
                     "mechanical_recycling":
                         [242, 302.5], "cement_co_processing": [0, 1E-6]},
                 # TODO: make sure that all data using tons are in metric
                 #  tons and not in US tons
                 lifetime_extension_years=[5, 15],
                 le_feasibility=0.55,
                 # TODO: report this parameter and source in Memo report
                 #  https://doi.org/10.1016/j.resconrec.2021.105439 assumption
                 #  is that early failure blades might be treated differently
                 #  than EOL blades
                 early_failure_share=0.03,
                 blade_types={"thermoset": True, "thermoplastic": True},
                 blade_types_dist_init={"thermoset": 1.0,
                                        "thermoplastic": 0.0},
                 tpb_bt_coeff={'w_bi': 1.00, 'w_a': 0.30, 'w_sn': 0.21,
                               'w_pbc': -0.32, 'w_p': 0.00, 'w_b': 0.00},
                 attitude_bt_parameters={
                     'mean': 0.5, 'standard_deviation': 0.1, 'min': 0,
                     'max': 1},
                 blade_costs={"thermoset": [50E3, 500E3],
                              "thermoplastic_rate": 0.953},
                 recyclers_states={
                     "dissolution": ["Texas", "Oklahoma", "North Carolina",
                                     "South Carolina", "Tennessee", "Ohio",
                                     "Ohio"],
                     "pyrolysis": ["South Carolina", "Tennessee"],
                     "mechanical_recycling": ["Iowa", "Texas", "Florida"],
                     "cement_co_processing": ["Missouri"]},
                 learning_parameter={
                     "dissolution": [-0.52, -0.39],
                     "pyrolysis": [-0.52, -0.39],
                     "mechanical_recycling": [-0.52, -0.39],
                     "cement_co_processing": [-1E-6, -0]},
                 blade_mass_fractions={
                     "steel": 0.05, "plastic": 0.09, "resin": 0.30,
                     "glass_fiber": 0.56},
                 rec_recovery_fractions={
                     "dissolution": {"steel": 1, "plastic": 1, "resin": 1,
                                     "glass_fiber": 1},
                     "pyrolysis": {"steel": 1, "plastic": 0, "resin": 0,
                                   "glass_fiber": 0.5},
                     "mechanical_recycling": {"steel": 1, "plastic": 1,
                                              "resin": 1, "glass_fiber": 1},
                     "cement_co_processing": {"steel": 1, "plastic": 0,
                                              "resin": 0, "glass_fiber": 1}}
                 ):
        """
        Initiate model.
        :param seed: number used to initialize the random generator
        :param manufacturers: number of manufacturers
        :param developers: number of developers
        :param recyclers: number of reyclers for each recycler type
        :param landfills: number of landfills
        :param small_world_networks: characteristics of the small-world 
        networks representing social relationships within agent types (if 
        rewiring prob set to 0: regular lattice, if set to 1: random network)
        :param external_files: dictionary mapping files to their variables
        :param growth_rates: states' wind capacity growth rates
        :param average_lifetime: wind turbines' average lifetime (years)
        :param weibull_shape_factor: parameter controlling curve's shape in 
        the Weibull function
        :param blade_size_to_mass_model: parameters for a power function 
        y=ax**b relating blade radius and blade mass where y is in metric tons 
        and x is in meters
        :param cap_to_diameter_model: parameters for a power function 
        converting turbine capacity to rotor diameter
        :param temporal_scope: simulation start and end year and past 
        installations considered
        :param blades_per_rotor: number of blades in rotors to compute blades'
        mass
        :param eol_pathways: end of life (eol) pathways available to wind 
        plant owner agents
        :param eol_pathways_dist_init: initial distribution of eol pathways 
        adoption in the population
        :param tpb_eol_coeff: regression coefficient in the theory of planned 
        behavior (TPB) model of eol behavior adoption
        :param attitude_eol_parameters: parameters for a truncated normal 
        distribution representing attitude among the population toward circular
        economy (CE) eol behaviors and to then infer non-circular behaviors
        :param choices_circularity: dictionary qualifying choices in terms of 
        circularity, this may affect agents decision (e.g., agents may hold a 
        different attitude depending on the choice circularity
        :param decommissioning_cost: cost of decommissioning wind turbines 
        ($/blade)
        :param lifetime_extension_costs: costs of feasibility assessment for
        the lifetime extension eol pathway ($/blade)
        :param rec_processes_costs: process costs of different recycling 
        pathways ($/metric ton), e.g., energy, labor etc. costs of pyrolysis
        :param landfill_costs: dictionary with landfill costs for each state
        :param transport_shreds: shredding_costs: grinding to 1-3 cm cost 
        ($/metric ton), transport_cost_shreds: transportation costs for 
        shredded blades ($/(metric ton-km))
        :param transport_segments: cutting_costs: cutting blades to segment 
        cost ($/metric ton), transport_cost_segment: transportation costs for 
        blade segments (2 per truck) ($/(truck_load-km)), length_segment: 
        length of blade segments once cut (m), segment_per_truck: number of 
        segment per truck
        :param transport_repair: transportation cost estimate for repair ($)
        :param eol_pathways_transport_mode: transportation mode for each eol
        pathway, if undefined, assumes a cost optimal choice between 
        transporting shreds or segments; 'transport_shreds', 
        'transport_segments', 'transport_shreds', and 'transport_repair' are 
        the only value accepted
        :param lifetime_extension_revenues: revenues from lifetime extension 
        ($/blade)
        :param rec_processes_revenues: revenue obtained from the various
        recycling pathways ($/metric ton)
        :param lifetime_extension_years: number of years a turbine lifetime is
        extended (years)
        :param le_feasibility: feasibility ratio of lifetime extension
        :param early_failure_share: share of early failure blade waste
        :param blade_types: type of blade available to wind plant developer 
        agents
        :param blade_types_dist_init: initial distribution of blade types (bt)
        adoption in the population
        :param tpb_bt_coeff: regression coefficient in the theory of planned 
        behavior (TPB) model of blade type adoption
        :param attitude_bt_parameters: parameters for a truncated normal 
        distribution representing attitude among the population toward circular
        economy (CE) bt behaviors and to then infer non-circular behaviors
        :param blade_costs: costs of different blade types ($/blade), 
        thermoplastic blades are 4.7% less expensive than thermoset blades
        :param recyclers_states: state where the recycling facilities are 
        located
        :param learning_parameter: learning parameters used to model the 
        learning effect for each recycling process
        :param blade_mass_fractions: material mass fractions of blades
        :param rec_recovery_fractions: material recovery fractions for each 
        recycling process
        """
        # Variables from inputs (value defined externally):
        self.seed = copy.deepcopy(seed)
        np.random.seed(self.seed)
        random.seed(self.seed)
        self.manufacturers = copy.deepcopy(manufacturers)
        self.developers = copy.deepcopy(developers)
        self.recyclers = copy.deepcopy(recyclers)
        self.landfills = copy.deepcopy(landfills)
        self.small_world_networks = copy.deepcopy(small_world_networks)
        self.external_files = copy.deepcopy(external_files)
        self.growth_rates = copy.deepcopy(growth_rates)
        self.average_lifetime = copy.deepcopy(average_lifetime)
        self.weibull_shape_factor = copy.deepcopy(weibull_shape_factor)
        self.blade_size_to_mass_model = copy.deepcopy(blade_size_to_mass_model)
        self.cap_to_diameter_model = copy.deepcopy(cap_to_diameter_model)
        self.temporal_scope = copy.deepcopy(temporal_scope)
        self.blades_per_rotor = copy.deepcopy(blades_per_rotor)
        self.eol_pathways = copy.deepcopy(eol_pathways)
        self.eol_pathways_dist_init = copy.deepcopy(eol_pathways_dist_init)
        self.tpb_eol_coeff = copy.deepcopy(tpb_eol_coeff)
        self.attitude_eol_parameters = copy.deepcopy(attitude_eol_parameters)
        self.choices_circularity = copy.deepcopy(choices_circularity)
        self.decommissioning_cost = copy.deepcopy(decommissioning_cost)
        self.lifetime_extension_costs = copy.deepcopy(lifetime_extension_costs)
        self.rec_processes_costs = copy.deepcopy(rec_processes_costs)
        self.landfill_costs = copy.deepcopy(landfill_costs)
        self.transport_shreds = copy.deepcopy(transport_shreds)
        self.transport_segments = copy.deepcopy(transport_segments)
        self.transport_repair = copy.deepcopy(transport_repair)
        self.eol_pathways_transport_mode = copy.deepcopy(
            eol_pathways_transport_mode)
        self.lifetime_extension_revenues = copy.deepcopy(
            lifetime_extension_revenues)
        self.rec_processes_revenues = copy.deepcopy(rec_processes_revenues)
        self.lifetime_extension_years = copy.deepcopy(lifetime_extension_years)
        self.le_feasibility = copy.deepcopy(le_feasibility)
        self.early_failure_share = copy.deepcopy(early_failure_share)
        self.blade_types = copy.deepcopy(blade_types)
        self.blade_types_dist_init = copy.deepcopy(blade_types_dist_init)
        self.tpb_bt_coeff = copy.deepcopy(tpb_bt_coeff)
        self.attitude_bt_parameters = copy.deepcopy(attitude_bt_parameters)
        self.blade_costs = copy.deepcopy(blade_costs)
        self.recyclers_states = copy.deepcopy(recyclers_states)
        self.learning_parameter = copy.deepcopy(learning_parameter)
        self.blade_mass_fractions = copy.deepcopy(blade_mass_fractions)
        self.rec_recovery_fractions = copy.deepcopy(rec_recovery_fractions)
        # Internal variables:
        self.clock = 0  # keep track of simulation time step
        self.unique_id = 0
        self.all_cap = 0
        self.all_waste = 0
        self.state_abrev = {
            'AL': 'Alabama', 'AZ': 'Arizona', 'AR': 'Arkansas',
            'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut',
            'DE': 'Delaware', 'FL': 'Florida', 'GA': 'Georgia', 'ID': 'Idaho',
            'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas',
            'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine',
            'MD': 'Maryland', 'MA': 'Massachusetts', 'MI': 'Michigan',
            'MN': 'Minnesota', 'MS': 'Mississippi', 'MO': 'Missouri',
            'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada',
            'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico',
            'NY': 'New York', 'NC': 'North Carolina', 'ND': 'North Dakota',
            'OH': 'Ohio', 'OK': 'Oklahoma', 'OR': 'Oregon',
            'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
            'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas',
            'UT': 'Utah', 'VT': 'Vermont', 'VA': 'Virginia',
            'WA': 'Washington', 'WV': 'West Virginia', 'WI': 'Wisconsin',
            'WY': 'Wyoming'}
        self.uswtdb = self.wind_plant_owner_data(
            self.external_files["uswtdb"], self.state_abrev,
            self.cap_to_diameter_model,
            self.temporal_scope['simulation_start'],
            self.temporal_scope['pre_simulation'])
        self.p_install_growth = self.p_install_growth_model(self.uswtdb)
        self.avg_p_cap = self.uswtdb['p_cap'].mean()
        self.states_cap = self.initial_dic_from_key_list(
            self.growth_rates.keys(), 0)
        self.states_waste = self.initial_dic_from_key_list(
            self.growth_rates.keys(), 0)
        self.additional_cap = self.initial_dic_from_key_list(
            self.growth_rates.keys(), 0)
        self.list_agent_states = []
        self.dict_agent_states = {}
        self.number_wpo_agent = 0
        self.list_init_eol_pathways = self.roulette_wheel_choice(
            self.remove_item_dic_from_boolean_dic(self.eol_pathways_dist_init,
                                                  self.eol_pathways),
            self.uswtdb.shape[0], True, [])
        self.list_init_eol_second_choice = self.list_init_eol_pathways.copy()
        self.list_init_blade_types = self.roulette_wheel_choice(
            self.remove_item_dic_from_boolean_dic(self.blade_types_dist_init,
                                                  self.blade_types),
            sum(self.developers.values()), True, [])
        self.list_init_bt_second_choice = self.list_init_blade_types.copy()
        self.list_add_agent_eol_path = []
        self.eol_pathway_dist_list = []
        self.eol_pathway_dist_dic = {}
        self.states_waste_eol_path = self.nested_init_dic(
            0, self.growth_rates.keys(), self.eol_pathways.keys())
        self.variables_recyclers = self.initial_dic_from_key_list(
            self.recyclers.keys(), [])
        self.variables_landfills = self.initial_dic_from_key_list(
            self.landfills.keys(), [])
        self.variables_developers = self.initial_dic_from_key_list(
            self.developers.keys(), [])
        self.variables_manufacturers = self.initial_dic_from_key_list(
            self.manufacturers.keys(), [])
        self.variables_additional_wpo = []
        self.regulators = len(self.growth_rates.keys())
        self.regulator_states_list = list(self.growth_rates.keys())
        self.regulations_enacted = self.nested_init_dic(
            False, self.choices_circularity.keys(), self.growth_rates.keys())
        self.bans_enacted = self.nested_init_dic(
            False, self.growth_rates.keys(), self.choices_circularity.keys())
        self.other_regulations_enacted = self.nested_init_dic(
            False, self.growth_rates.keys(), self.choices_circularity.keys())
        self.le_characteristics = []
        self.eol_pathway_adoption = self.initial_dic_from_key_list(
            self.eol_pathways.keys(), 0)
        self.landfill_state_list = list(self.landfill_costs.keys())
        self.all_additional_cap_installed = False
        self.list_recycler_types = self.roulette_wheel_choice(
            self.recyclers, sum(self.recyclers.values()), True, [])
        self.list_manufacturer_types = self.roulette_wheel_choice(
            self.manufacturers, sum(self.manufacturers.values()), True, [])
        self.tp_blade_manufactured = 0
        self.tp_blade_demanded = 0
        self.dissolution_available = {}
        self.blade_type_capacities = self.nested_init_dic(
            0, self.growth_rates.keys(), self.blade_types.keys())
        self.waste_rec_land = {}
        self.average_recycler_costs = self.initial_dic_from_key_list(
            self.eol_pathways.keys(), 0)
        self.recovered_materials = self.initial_dic_from_key_list(
            self.blade_mass_fractions.keys(), 0)
        # Computing transportation distances:
        self.state_distances = \
            pd.read_csv(self.external_files["state_distances"])
        self.state_dis_matrix = self.state_distances.to_numpy()
        self.states = self.state_distances.columns.to_list()
        self.states_graph = nx.from_numpy_matrix(self.state_dis_matrix)
        self.nodes_states_dic = \
            dict(zip(list(self.states_graph.nodes),
                     list(self.state_distances)))
        self.states_graph = nx.relabel_nodes(self.states_graph,
                                             self.nodes_states_dic)
        self.all_shortest_paths_or_trg = self.compute_all_distances(
            self.states, self.states_graph)
        # Creating agents and social networks:
        self.schedule = BaseScheduler(self)
        self.G_rec, self.grid_rec, self.schedule_rec = \
            self.network_grid_schedule_agents(
                sum(self.recyclers.values()),
                self.small_world_networks["recyclers"]["node_degree"],
                self.small_world_networks["recyclers"]["rewiring_prob"],
                sum(self.recyclers.values()), Recycler)
        self.G_land, self.grid_land, self.schedule_land = \
            self.network_grid_schedule_agents(
                sum(self.landfills.values()),
                self.small_world_networks["landfills"]["node_degree"],
                self.small_world_networks["landfills"]["rewiring_prob"],
                sum(self.landfills.values()), Landfill)
        self.G_man, self.grid_man, self.schedule_man = \
            self.network_grid_schedule_agents(
                sum(self.manufacturers.values()),
                self.small_world_networks["manufacturers"]["node_degree"],
                self.small_world_networks["manufacturers"]["rewiring_prob"],
                sum(self.manufacturers.values()), Manufacturer)
        self.G_dev, self.grid_dev, self.schedule_dev = \
            self.network_grid_schedule_agents(
                sum(self.developers.values()),
                self.small_world_networks["developers"]["node_degree"],
                self.small_world_networks["developers"]["rewiring_prob"],
                sum(self.developers.values()), Developer)
        self.G_reg, self.grid_reg, self.schedule_reg = \
            self.network_grid_schedule_agents(
                self.regulators,
                self.small_world_networks["regulators"]["node_degree"],
                self.small_world_networks["regulators"]["rewiring_prob"],
                self.regulators, Regulator)
        self.first_wpo_id = self.unique_id
        self.G_wpo, self.grid_wpo, self.schedule_wpo = \
            self.network_grid_schedule_agents(
                self.compute_max_network_size(
                    self.uswtdb, self.temporal_scope['simulation_start'],
                    self.temporal_scope['simulation_end'],
                    self.p_install_growth),
                self.small_world_networks[
                    "wind_plant_owners"]["node_degree"],
                self.small_world_networks[
                    "wind_plant_owners"]["rewiring_prob"],
                self.uswtdb.shape[0], WindPlantOwner)
        self.additional_id = self.first_wpo_id + self.uswtdb.shape[0]
        # Create data collectors:
        self.model_reporters = {
            "Year": lambda a:
            self.clock + self.temporal_scope['simulation_start'],
            "Cumulative capacity (MW)": lambda a: self.all_cap,
            "State cumulative capacity (MW)": lambda a: str(self.states_cap),
            "Cumulative waste (metric tons)": lambda a: self.all_waste,
            "State waste (metric tons)": lambda a: str(self.states_waste),
            "State waste - eol pathways (metric tons)":
                lambda a: str(self.states_waste_eol_path),
            "Number wpo agents": lambda a: self.number_wpo_agent,
            "eol pathway adoption": lambda a: str(self.eol_pathway_adoption),
            "Blade type adoption (MW)":
                lambda a: str(self.blade_type_capacities),
            "Average recycling costs ($/metric ton)":
                lambda a: str(self.average_recycler_costs),
            "Recovered materials (metric tons)":
                lambda a: str(self.recovered_materials)}
        self.agent_reporters = {
            "State": lambda a: getattr(a, "t_state", None),
            "Capacity (MW)": lambda a: getattr(a, "p_cap", None),
            "Cumulative waste (metric tons)": lambda a: getattr(
                a, "cum_waste", None),
            "Mass conversion factor": lambda a:
            getattr(a, "mass_conv_factor", None)}
        self.data_collector = DataCollector(
            model_reporters=self.model_reporters,
            agent_reporters=self.agent_reporters)

    def network_grid_schedule_agents(self, num_nodes, node_degree,
                                     rewiring_prob, num_agents, agent_type,
                                     **kwargs):
        """
        Creates the network of agents, links it to Mesa.space grid object, and
        schedule the agents
        :param num_nodes: number of nodes in the network
        :param node_degree: average node degree in the network
        :param rewiring_prob: probability of rewiring a given edge
        :param num_agents: number og agents to schedule
        :param agent_type: type of agents to schedule
        :return: the network, the grid and the schedule
        """
        network = self.creating_social_network(num_nodes, node_degree,
                                               rewiring_prob, self.seed)
        grid = NetworkGrid(network)
        schedule = RandomActivation(self)
        self.creating_agents(num_agents, network, grid, schedule, agent_type,
                             **kwargs)
        return network, grid, schedule,

    def compute_all_distances(self, states, graph):
        """
        Compute distances for all shortest paths between a set of targets
        (origins) and all possible origins (targets).
        :param states: set of targets (origins)
        :param graph: a graph representing the agents' environment
        :return: a panda frames with index and columns equal to targets
        and destinations names and values equal to shortest path distances
        between any given target/origin combination.
        """
        all_shortest_paths_or_trg = np.zeros([len(states), len(graph)])
        for count, i in enumerate(states):
            target_states = [i]
            dist_list = []
            dist_list = self.shortest_paths(graph, target_states, dist_list)
            all_shortest_paths_or_trg[count] = dist_list
        all_shortest_paths_or_trg = pd.DataFrame(
            all_shortest_paths_or_trg, index=states, columns=graph.nodes)
        return all_shortest_paths_or_trg

    def shortest_paths(self, graph, target_states, distances_to_target):
        """
        Compute shortest paths between chosen origin states and targets with
        the Dijkstra algorithm.
        :param graph: graph from which shortest paths need to be computed
        :param target_states: target (or origin) to compute shortest paths,
        if the value is smaller than the graph number of nodes, the the output
        is a rectangular matrix
        :param distances_to_target: an empty list that will be filled with
        shortest paths
        :return distances_to_target: a list of shortest path between a target
        (origin) and all origins (targets) in the graph
        """
        for i in self.states_graph.nodes:
            shortest_paths = []
            for j in target_states:
                shortest_paths.append(
                    nx.shortest_path_length(graph, source=i,
                                            target=j, weight='weight',
                                            method='dijkstra'))
            shortest_paths_closest_target = min(shortest_paths)
            if shortest_paths_closest_target == 0:
                adjacency_matrix = nx.adjacency_matrix(graph).toarray()
                shortest_paths_closest_target = np.nanmean(
                    np.where(adjacency_matrix != 0, adjacency_matrix,
                             np.nan)) / 2
            distances_to_target.append(shortest_paths_closest_target)
        return distances_to_target

    @staticmethod
    def creating_social_network(nodes, node_degree, rewiring_prob, seed):
        """
        Set up model's social networks with the Watts & Strogatz algorithm.
        :param nodes: number of nodes in the graph
        :param node_degree: node degree of the equivalent regular lattice
        :param rewiring_prob: probability of rewiring a given edge
        :param seed: random seed for the small-world network
        :return social_network: a graph representing agents' social network
        """
        social_network = nx.watts_strogatz_graph(nodes, node_degree,
                                                 rewiring_prob,
                                                 seed=random.seed(seed))
        return social_network

    @staticmethod
    def compute_max_network_size(uswtdb, simulation_start, simulation_end,
                                 coefficient):
        """
        Compute the number of nodes for the graph of potential maximum length
        during the simulation.
        :param uswtdb: us wind turbine database
        :param simulation_start: starting year of the simulation
        :param simulation_end: ending year of the simulation
        :param coefficient: slope from a linear regression model determining
        the number yearly installed wind projects
        :return: the number of nodes for the graph of potential maximum length
        """
        initial_nodes = uswtdb.shape[0]
        years = simulation_end - simulation_start
        additional_nodes = coefficient * years
        total_nodes = int(initial_nodes + additional_nodes)
        return total_nodes

    def creating_agents(self, num_agents, social_network, grid, schedule,
                        agent_type, **kwargs):
        """
        Create agents and assign their attributes. Link agents to nodes in the
        social network with the node labels equal to the agent unique id.
        :param num_agents: number of agents at the beginning of the simulation
        :param social_network: social network linking agents
        :param grid: equivalent graph in Mesa's space
        :param schedule: Mesa scheduler of the agent type
        :param agent_type: name of the agent type, must be similar to the
        agent class's name
        :param kwargs: additional parameters
        """
        for node in social_network:
            if node < num_agents:
                a = agent_type(self.unique_id, self, **kwargs)
                schedule.add(a)
                grid.place_agent(a, node)
                self.schedule.add(a)
            self.unique_id += 1

    def adding_agents(self, num_agents, grid, schedule, agent_type, **kwargs):
        """
        Add agents to the network, the global schedule and a specific schedule
        during the simulation.
        :param num_agents: number of agents to add
        :param grid: the network relating the agents
        :param schedule: the schedule of the agent type
        :param agent_type: the agent type
        :param kwargs: additional parameters
        :return: add the agent to the model
        """
        for agent in range(num_agents):
            a = agent_type(self.additional_id, self, **kwargs)
            schedule.add(a)
            grid.place_agent(a, (self.additional_id - self.first_wpo_id))
            self.schedule.add(a)
            self.additional_id += 1

    @staticmethod
    def wind_plant_owner_data(database, state_abrev, cap_to_diameter_model,
                              start_year, pre_simulation):
        """
        Convert database to a pandas DataFrame and select relevant data
        :param database: the csv file of the US wind turbine database
        uswtdb_v3_3_20210114 (https://doi.org/10.5066/F7TX3DN0)
        :param state_abrev: dictionary to convert state abbreviations to
        full names
        :param cap_to_diameter_model: parameters for a power function used to
        fill up data gaps in the uswtdb t_rd column
        :param start_year: simulation start year
        :param pre_simulation: historical years considered
        :return: pandas DataFrame for use by wind plant owners
        """
        uswtdb = pd.read_csv(database, dtype={'t_manu': 'object',
                                              't_model': 'object'})
        uswtdb = uswtdb[(uswtdb['p_year'] >= pre_simulation) &
                        (uswtdb['p_year'] <= start_year)]
        uswtdb = uswtdb.groupby('p_name').agg(
            lambda x: x.head(1) if x.dtype == 'object' else
            x.mean()).reset_index()
        uswtdb = uswtdb[['p_name', 'p_year', 'p_tnum', 't_state', 't_rd',
                         't_cap']]
        uswtdb['t_cap'] /= 1000  # convert t_cap from kW to MW
        uswtdb['p_cap'] = uswtdb['t_cap'] * uswtdb['p_tnum']
        uswtdb = uswtdb[(uswtdb.t_state != 'AK') & (uswtdb.t_state != 'HI') &
                        (uswtdb.t_state != 'PR') & (uswtdb.t_state != 'GU')]
        uswtdb = uswtdb[uswtdb['p_cap'].notna()].reset_index()
        uswtdb['t_rd'].fillna(
            cap_to_diameter_model['coefficient'] *
            uswtdb['t_cap']**cap_to_diameter_model['power'], inplace=True)
        uswtdb = uswtdb.replace({'t_state': state_abrev})
        return uswtdb

    @staticmethod
    def p_install_growth_model(uswtdb):
        """
        Compute the number of yearly new wind project (agents) with a linear
        regression model.
        :param uswtdb: us wind turbine database
        :return: number of yearly new wind project (agents)
        """
        year_count = uswtdb['p_year'].value_counts(sort=False).to_frame()
        year_count = year_count.sort_index(ascending=True)
        year_count['cum_install'] = year_count['p_year'].cumsum()
        x = year_count.index.tolist()
        y = year_count['cum_install'].tolist()
        result = scipy.stats.linregress(x, y)
        p_install_growth = result.slope
        min_install = uswtdb['t_state'].nunique()
        if p_install_growth < min_install:
            p_install_growth = min_install
            warnings.warn("There are less additional installation than "
                          "states with growth. The model added additional "
                          "installations to balance.")
        return int(p_install_growth)

    @staticmethod
    def cumulative_capacity_growth(states_cap, growth_rates, additional_cap):
        """
        Grow the installed capacities according to growth rate
        :param states_cap: dictionary of wind power capacity in each state
        :param growth_rates: growth rate of the cumulative installed capacity
        :param additional_cap: dictionary to output
        :return output a dictionary containing the states' additional capacity
        for the time step of the simulation
        """
        for state in states_cap.keys():
            additional_capacity = states_cap[state] * growth_rates[state]
            additional_cap[state] = additional_capacity
        additional_cap = {key: value for (key, value) in
                          additional_cap.items() if value != 0}
        return additional_cap

    def additional_agent_state(self, additional_cap, p_install_growth):
        """
        Compute a list of state names, with several copies for certain names
        :param additional_cap: a dictionary containing the states' additional
        capacity for the time step of the simulation
        :param p_install_growth: number of agents to add
        :return: a list containing state names and duplicates, with relative
        frequencies depending on the capacity growths in the states
        """
        state_add_cap_prop = {
            key: (value / sum(additional_cap.values())) for (key, value) in
            additional_cap.items()}
        list_agent_states = list(state_add_cap_prop.keys())
        if len(list_agent_states) < p_install_growth:
            num_choices = p_install_growth - len(list_agent_states)
            list_agent_states = self.roulette_wheel_choice(
                state_add_cap_prop, num_choices, False, list_agent_states)
        return list_agent_states

    def roulette_wheel_choice(self, dic_frequencies, num_choices,
                              deterministic, list_choice):
        """
        Make a choice according to a roulette wheel process
        :param dic_frequencies: a dictionary containing frequencies (determines
        the size of the wedges in the roulette wheel)
        :param num_choices: number of choices (number of roulette draws)
        :param deterministic: if True randomly select the pick (where the ball
        falls on the wheel), otherwise choose the pick as to distribute values
        to exactly respect the dictionary's frequencies
        :param list_choice: the list of choices distributed according to the
        roulette wheel draws
        :return: the list of choices list_choice
        """
        cum_freq = self.dic_cumulative_frequencies(dic_frequencies)
        max_cum_freq = max(cum_freq.values())
        for i in range(num_choices):
            if deterministic:
                pick = i / num_choices * max_cum_freq
            else:
                pick = random.uniform(0, max_cum_freq)
            choice = self.roulette_wheel(pick, cum_freq)
            list_choice.append(choice)
        random.shuffle(list_choice)
        return list_choice

    @staticmethod
    def dic_with_list_item_frequency(input_list):
        """
        Dictionary containing the values of a list as keys and their
        frequencies as values
        :param input_list: the list to transform in a dictionary with
        frequencies
        :return: dictionary with values and their frequencies
        """
        output_dic = {}
        for item in input_list:
            if item in output_dic:
                output_dic[item] += 1
            else:
                output_dic[item] = 1
        return output_dic

    @staticmethod
    def waste_generation(start_year, clock, p_year, p_cap_waste, avg_lifetime,
                         weibull_shape_factor):
        """
        Weibull function generating waste: simulate wind turbine failure rate
        :param start_year: starting year for waste generation
        :param clock: model clock
        :param p_year: agent installation year
        :param p_cap_waste: agent capacity to apply function to
        :param avg_lifetime: average lifetime of wind turbines
        :param weibull_shape_factor: factor controlling shape of Weibull curve
        :return: Yearly waste from agent EOL Wind turbine
        """
        correction_year = start_year - p_year
        waste = \
            p_cap_waste * (1 - e**(-(((clock + correction_year) /
                                      avg_lifetime)**weibull_shape_factor)))
        return waste

    @staticmethod
    def initial_dic_from_key_list(key_list, initial_value):
        """
        Create dictionary with keys taken from a list and an initial value
        :param key_list: the list of keys
        :param initial_value: initial value (or object) for the dictionary
        :return: the empty dictionary with corresponding keys
        """
        initial_dic = {}
        for i in key_list:
            initial_value_copy = copy.copy(initial_value)
            initial_dic[i] = initial_value_copy
        return initial_dic

    def nested_init_dic(self, initial_value, list_keys1, list_keys2):
        """
        Creates a nested dictionary (2 levels) with an initial object
        :param initial_value: the initial value for the nested dictionary, it
        can be an integer, a list, a float, etc.
        :param list_keys1: lists of keys for the nested dictionary
        :param list_keys2: lists of keys for the nested dictionary
        :return: nested dictionary with keys and values determined from inputs
        """
        dic = {}
        list_lists = [list_keys1, list_keys2]
        for i in range(len(list_lists) - 1):
            dic = self.initial_dic_from_key_list(list_lists[i], initial_value)
            for key in dic.keys():
                # noinspection PyTypeChecker
                dic[key] = self.initial_dic_from_key_list(
                    list_lists[i + 1], initial_value)
        return dic

    @staticmethod
    def roulette_wheel(pick, cum_prob_dic):
        """
        Apply a roulette wheel process to output an element according to its
        frequency
        :param pick: the value from which the corresponding dictionary key
        need to be returned (the ball in the roulette)
        :param cum_prob_dic: a dictionary containing cumulative frequencies
        (the wedges in the roulette)
        :return: the chosen key depending on the pick value (where the ball
        stopped)
        """
        current = 0
        for key, value in cum_prob_dic.items():
            current += value
            if value > pick:
                return key

    @staticmethod
    def dic_cumulative_frequencies(dic):
        """
        From a dictionary containing keys and their frequencies, output a
        dictionary with their cumulative frequencies
        :param dic: the input dictionary with frequencies of keys
        :return: an output dictionary with cumulative frequencies
        """
        list_cumprob = np.cumsum(list(dic.values()))
        dic_cumprob = dict(zip(dic.keys(), list_cumprob))
        return dic_cumprob

    @staticmethod
    def remove_item_dic_from_boolean_dic(dic, boolean_dic):
        """
        Remove keys, values from a dictionary if the key in another dictionary
        is false
        :param dic: dictionary to modify
        :param boolean_dic: dictionary of booleans, (with keys matching the
        dictionary to modify)
        :return: modified dictionary
        """
        for key, value in boolean_dic.items():
            if not value:
                dic.pop(key)
        return dic

    @staticmethod
    def attitude(ce_att_level, conv_att_level, dic_choices,
                 choices_circularity):
        """
        Computes the  TPB attitude scores for each circular and non-circular
        choices
        :param ce_att_level: attitude level for circular choices
        :param conv_att_level: attitude level for non circular choices
        :param dic_choices: dictionary with the different choices
        :param choices_circularity: dictionary associating choice and a boolean
        with True when the choice is considered circular and False otherwise
        :return: the attitude scores for each choice
        """
        scores = {}
        circular_choices = {key: value for (key, value) in
                            choices_circularity.items() if value}
        for key in dic_choices.keys():
            if key in circular_choices.keys():
                scores[key] = ce_att_level
            else:
                scores[key] = conv_att_level
        return scores

    def subjective_norms(self, grid, adopted_choice, position, dic_choices):
        """
        Computes the TPB subjective norms scores for each circular and
        non-circular choices as measured by the proportion of agents that have
        already adopted a given choice
        :param grid: network grid connecting agents
        :param adopted_choice: name of the type of choice to be made (e.g., eol
        choice)
        :param position: position of the agent in the network
        :param dic_choices: dictionary with the different choices
        :return: the subjective norms scores for each choice
        """
        scores = {}
        neighbors_nodes = grid.get_neighbors(position, include_center=False)
        neighbors_nodes = [x for x in neighbors_nodes
                           if not grid.is_cell_empty(x)]
        for key in dic_choices.keys():
            list_agent_w_key = [
                agent for agent in
                grid.get_cell_list_contents(neighbors_nodes) if
                getattr(agent, adopted_choice) == key]
            score_key = self.safe_div(len(list_agent_w_key),
                                      len(neighbors_nodes))
            scores[key] = score_key
        return scores

    def perceived_behavioral_control_and_barrier(self, value_choices):
        """
        Computes the TPB perceived behavioral control (or barriers) scores for
        each circular and non-circular choices as measured by their percentage
        of the maximum value (highest cost (or distance))
        :param value_choices: the cost (or distance) of each choice
        :return: the perceived behavioral control (or barriers) scores for
        each choice
        """
        scores = {}
        max_cost = max(abs(i) for i in value_choices.values())
        for key in value_choices.keys():
            score_key = self.safe_div(value_choices[key], max_cost)
            score_key = max(score_key, 0)
            scores[key] = score_key
        return scores

    def pressure(self, state, regulations):
        """
        Computes the TPB pressure scores for each circular and non-circular
        choices as measured by the weighted (by the distance to the agent)
        average of states that have enacted some regulations
        :param state: state of the agent
        :param regulations: a nested dictionary of choices and states that
        containing Booleans with True when the regulator in the state has
        enacted regulation(s) for the given choice and False otherwise
        :return: the pressure scores for each choice
        """
        scores = {}
        all_or_trg_distances = self.all_shortest_paths_or_trg[state]
        max_dist = max(all_or_trg_distances)
        for key, value in regulations.items():
            list_state_w_regulation = [
                key for key, val in value.items() if val]
            weighted_sum = sum(
                [(max_dist - all_or_trg_distances[item]) / max_dist for
                 item in list_state_w_regulation])
            pressure_max = sum(
                [(max_dist - all_or_trg_distances[item]) / max_dist for
                 item in value.keys()])
            scores[key] = weighted_sum / pressure_max
        return scores

    def theory_planned_behavior_model(
            self, tpb_weights, ce_att_level, conv_att_level, dic_choices,
            choices_circularity, grid, adopted_choice, position, cost_choices,
            barrier_choices, state, regulations):
        """
        Compute the behavior scores for each choice depending on the elements
        of the TPB: attitude, subjectives norms, perceived behavioral control,
        barriers, and pressure; the behavior with the highest is adopted
        while a second choice is also selected to account for limited technical
        feasibility of some choices (e.g., lifetime extension)
        :param tpb_weights: weights of the different factors in the TPB
        :param ce_att_level: attitude level for circular choices
        :param conv_att_level: attitude level for non circular choices
        :param dic_choices: dictionary with the different choices
        :param choices_circularity: dictionary associating choice and a boolean
        with True when the choice is considered circular and False otherwise
        :param grid: network grid connecting agents
        :param adopted_choice: name of the type choice to be made (e.g., eol
        choice)
        :param position: position of the agent in the network
        :param cost_choices: the cost of each choice
        :param barrier_choices: the distance of each choice
        :param state: state of the agent
        :param regulations: a nested dictionary of choices and states that
        containing Booleans with True when the regulator in the state has
        enacted regulation(s) for the given choice and False otherwise
        :return: the two behaviors with the highest scores
        """
        scores_sn = self.subjective_norms(grid, adopted_choice, position,
                                          dic_choices)
        scores_a = self.attitude(ce_att_level, conv_att_level, dic_choices,
                                 choices_circularity)
        scores_pbc = self.perceived_behavioral_control_and_barrier(
            cost_choices)
        scores_b = self.perceived_behavioral_control_and_barrier(
            barrier_choices)
        scores_p = self.pressure(state, regulations)
        scores_behaviors = {}
        for key, value in dic_choices.items():
            scores_behaviors[key] = tpb_weights['w_bi'] * (
                    tpb_weights['w_sn'] * scores_sn[key] +
                    tpb_weights['w_a'] * scores_a[key] +
                    tpb_weights['w_pbc'] * scores_pbc[key]) + \
                    tpb_weights['w_b'] * scores_b[key] + \
                    tpb_weights['w_p'] * scores_p[key]
            if not value:
                scores_behaviors.pop(key)
        first_choices = [keys for keys, values in scores_behaviors.items() if
                         values == max(scores_behaviors.values())]
        # if two behavior equally score the highest, choose randomly
        random.shuffle(first_choices)
        first_choice = first_choices[0]
        scores_behaviors.pop(first_choice)
        second_choices = [keys for keys, values in scores_behaviors.items() if
                          values == max(scores_behaviors.values())]
        random.shuffle(second_choices)
        second_choice = second_choices[0]
        return first_choice, second_choice

    @staticmethod
    def lifetime_extension(eol_pathway, initial_lifetime, le_feas_years):
        """
        Add a number of years to the average lifetime of turbines and compute
        the share of turbines that can feasibly have their life extended in the
        wind farm of wpo
        :param eol_pathway: adopted eol pathway of the agent
        :param initial_lifetime: initial average lifetime
        :param le_feas_years: lifetime extension characteristics taken from
        wind plant developer agents
        :return: the initial lifetime with additional years if lifetime
        extension is adopted and the share of turbines that are concerned
        """
        feasibility = le_feas_years[0]
        years_extended = le_feas_years[1]
        if eol_pathway == 'lifetime_extension':
            return (initial_lifetime + years_extended), (1 - feasibility)
        else:
            return initial_lifetime, 0

    def assign_agents_to_each_other(self, list_variables_to_assign,
                                    number_agent, number_agent_assigned,
                                    list_agent_assigned, exclusive_assignment):
        """
        Function to assign agents of different types to each others, thereby
        representing relationships between agents of different types (e.g.,
        contractual or B2B, B2C relations); with this function, the variables
        from an agent that are needed by another can be accessed by the latter
        :param list_variables_to_assign: list of tuples of variables of
        agent of one type to assign to another type of agent
        :param number_agent: number of agents that will get agent variables
        from the other agent type
        :param number_agent_assigned: number of agent to assign to the other
        agent type
        :param list_agent_assigned: the output list of assigned agent variables
        :param exclusive_assignment: determine if the assigned agent can only
        be assigned once or not
        :return: the output list of assigned agent variables (list of tuples)
        """
        agents_to_assign = int(
            np.ceil(number_agent_assigned / number_agent))
        for i in range(agents_to_assign):
            if list_variables_to_assign:
                # A tuple is appended to the list with x, y... variables of
                # assigned agents
                agent_assigned = self.assign_elements_from_list(
                    list_variables_to_assign, exclusive_assignment)
                list_agent_assigned.append(agent_assigned)
        return list_agent_assigned

    @staticmethod
    def assign_elements_from_list(list_elements, exclusive_assignment):
        """
        Choose an element from a list, either randomly or the last element of
        the list (and remove it from the list)
        :param list_elements: list of elements to choose from
        :param exclusive_assignment: if True the element is returned and
        removed from the list, if False the element is randomly chosen from the
        list and the list is left intact
        :return: the chosen element
        """
        if exclusive_assignment:
            element = list_elements.pop()
        else:
            element = random.choice(list_elements)
        return element

    @staticmethod
    def random_pick_dic_key(dic_to_pick_key_from):
        """
        Randomly select a key in a dictionary
        :param dic_to_pick_key_from: dictionary from which to select key
        :return: the selected key
        """
        list_to_shuffle = list(dic_to_pick_key_from.keys())
        random.shuffle(list_to_shuffle)
        pick = list_to_shuffle[0]
        return pick

    @staticmethod
    def boolean_dic_based_on_dicts(dic_to_modify, value_to_change, modifier,
                                   *args):
        """
        Build a dictionary with Booleans based on values in other dictionaries;
        other dictionaries should also be Booleans
        :param dic_to_modify: the dictionary to modify
        :param value_to_change: the value to change from the dictionaries
        :param modifier: modify the value of the dictionary dic_to_modify
        :param args: dictionaries which determine what values are modified in
        dic_to_modify
        :return: the modified dictionary
        """
        for arg in args:
            if any(x == value_to_change for x in arg.values()):
                for key, value in arg.items():
                    if value == value_to_change:
                        dic_to_modify[key] = bool(value * modifier)
        return dic_to_modify

    @staticmethod
    def filter_list(input_list, filtered_out_value):
        """
        Filter out a given value from list if list contains more than 1 value,
        otherwise return input list (avoids empty lists)
        :param input_list: list from which the value should be filtered out
        :param filtered_out_value: the value to filter out from list
        :return: filtered out value
        """
        output = list(filter(lambda x: x != filtered_out_value, input_list))
        if output:
            return output
        else:
            return input_list

    @staticmethod
    def safe_div(x, y):
        """
        Division that return 0 if the denominator is equal to 0
        :param x: numerator
        :param y: denominator
        :return: value of the division being 0 if the denominator is 0
        """
        if y == 0:
            return 0
        return x / y

    @staticmethod
    def trunc_normal_distrib_draw(a, b, loc, scale):
        """
        Draw a value from a truncated normal distribution
        :param a: minimum of the range from where to draw
        :param b: maximum of the range from where to draw
        :param loc: mean of the distribution
        :param scale: standard deviation of the distribution
        :return: drawn value
        """
        distribution = truncnorm(a, b, loc, scale)
        draw = float(distribution.rvs(1))
        return draw

    @staticmethod
    def symetric_triang_distrib_draw(min_value, max_value):
        """
        Draw a value from a symetric triangular distribution
        :param min_value: minimum of the range from where to draw
        :param max_value: maximum of the range from where to draw
        :return: drawn value
        """
        mode = (max_value + min_value) / 2
        draw = np.random.triangular(min_value, mode, max_value)
        return draw

    @staticmethod
    def most_common_element_list(input_list):
        """
        Return the most common element in a list (mode), in case of a draw the
        element that first appear in the list is returned
        :param input_list: list from which the most common element needs to
        be determined
        :return: the most common element
        """
        output = max(set(input_list), key=input_list.count)
        return output

    def reinitialize_global_variables_wpo(self):
        """
        Re-initialize yearly variables
        """
        self.number_wpo_agent = 0
        self.eol_pathway_dist_list = []
        self.eol_pathway_adoption = self.initial_dic_from_key_list(
            self.eol_pathways.keys(), 0)
        self.waste_rec_land = self.initial_dic_from_key_list(
            self.waste_rec_land.keys(), 0)

    def reinitialize_global_variables_rec_land_reg_dev(self):
        """
        Re-initialize yearly variables
        """
        self.variables_recyclers = self.initial_dic_from_key_list(
            self.recyclers.keys(), [])
        self.variables_landfills = self.initial_dic_from_key_list(
            self.landfills.keys(), [])
        self.regulations_enacted = self.nested_init_dic(
            False, self.choices_circularity.keys(), self.growth_rates.keys())
        self.le_characteristics = []
        self.dissolution_available = {}

    def reinitialize_global_variables_dev_man_rec(self):
        """
        Re-initialize yearly variables
        """
        self.variables_additional_wpo = []
        self.tp_blade_manufactured = 0
        self.tp_blade_demanded = 0
        self.average_recycler_costs = self.initial_dic_from_key_list(
            self.eol_pathways.keys(), 0)

    def update_model_variables(self):
        """
        Update model variables
        """
        self.all_additional_cap_installed = False
        self.list_agent_states = \
            self.additional_agent_state(self.additional_cap,
                                        self.p_install_growth)
        self.dict_agent_states = self.dic_with_list_item_frequency(
            self.list_agent_states)
        self.eol_pathway_dist_dic = self.dic_with_list_item_frequency(
            self.eol_pathway_dist_list)
        # Extend initial eol pathways distribution as based on current adoption
        self.list_add_agent_eol_path = self.roulette_wheel_choice(
            self.eol_pathway_dist_dic, self.p_install_growth, False, [])

    def step(self):
        """
        Advance the model by one step and collect data.
        """
        self.data_collector.collect(self)
        self.reinitialize_global_variables_wpo()
        self.schedule_wpo.step()
        self.reinitialize_global_variables_rec_land_reg_dev()
        self.schedule_man.step()
        self.schedule_dev.step()
        self.reinitialize_global_variables_dev_man_rec()
        self.schedule_rec.step()
        self.schedule_land.step()
        self.schedule_reg.step()
        self.schedule.step()
        self.update_model_variables()
        self.adding_agents(self.p_install_growth, self.grid_wpo,
                           self.schedule_wpo, WindPlantOwner)
        self.clock += 1
