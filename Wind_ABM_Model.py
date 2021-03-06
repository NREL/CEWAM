# -*- coding:utf-8 -*-
"""
Created on December 31 2020

@author Julien Walzberg - Julien.Walzberg@nrel.gov

Model - Circular Economy Wind Agent-based Model (CEWAM)
This module contains the model class that creates and activates agents. The
module also defines inputs (default values can be changed by user) and collect
outputs.
"""

# TODO: Next steps:
#  1) Re-write all unittests and missing unittest for all agents
#  2) More unittests:
#    i) for recycler and other agents similar to recycler write
#    unittests to check initial distribution of types
#    ii) also try to build unittests to check that outputs are correct
#    ("mini extreme scenario" to test that the model output intermediate
#    variables (like adoption of pathways and such correctly)
#  3) Scenario analysis:
#    * Different wind power capacity projections: growth rates from
#    95-by-35.Adv and 95-by-35+Elec.Adv+DR scenarios in: C:\Users\jwalzber\
#    Documents\Winter21\Wind_ABM\Modeling\Data\ProjectedCapacity
#    * Additional recycling facilities and/or lower recycling costs
#  4) A reinforcement learning could be used in the future (long term)
#  6) (Optional) Improving code:
#    i) Find where the code is slow
#    ii) generate documentation using Sphinx and autodoc or something else

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
                 batch_run=False,
                 calibration=1,
                 calibration_2=1,
                 calibration_3=1,
                 calibration_4=1,
                 calibration_5=1,
                 calibration_6=1,
                 calibration_7=1,
                 calibration_8=1,
                 calibration_9=1,
                 manufacturers={
                     "wind_blade": 5, "plastics_n_boards": 100, "cement": 97},
                 developers={'lifetime_extension': 10},
                 recyclers={
                     "dissolution": 6, "pyrolysis": 2,
                     "mechanical_recycling": 3, "cement_co_processing": 1},
                 small_world_networks={
                     "wind_plant_owners": {
                         "node_degree": 15, "rewiring_prob": 0.1},
                     "developers": {"node_degree": 5, "rewiring_prob": 0.1},
                     "recyclers": {"node_degree": 5, "rewiring_prob": 0.1},
                     "manufacturers": {"node_degree": 15,
                                       "rewiring_prob": 0.1},
                     "original_equipment_manufacturer": {
                         "node_degree": 4, "rewiring_prob": 1},
                     "landfills": {"node_degree": 5, "rewiring_prob": 0.1},
                     "regulators": {"node_degree": 5, "rewiring_prob": 0.1}},
                 external_files={
                     "state_distances": "state_centroid_distances.csv",
                     "detailed_distances": "transport_distances.csv",
                     "uswtdb": "uswtdb_v3_3_20210114.csv", "projections":
                         "nrel_mid_case_projections.csv",
                     "wbj_database": "WBJ Landfills 2020.csv"},
                 average_lifetime={'thermoset': [20.0, 20.0001],
                                   'thermoplastic': [20.0, 20.0001]},
                 weibull_shape_factor=2.2,
                 blade_size_to_mass_model={'coefficient': 0.0026,
                                           'power': 2.1447},
                 cap_to_diameter_model={'coefficient': 57,
                                        'power': 0.44},
                 temporal_scope={
                     'pre_simulation': 2000, 'simulation_start': 2020,
                     'simulation_end': 2050},
                 blades_per_rotor=3,
                 eol_pathways={
                     "lifetime_extension": True, "dissolution": False,
                     "pyrolysis": True, "mechanical_recycling": True,
                     "cement_co_processing": True, "landfill": True},
                 eol_pathways_dist_init={
                     "lifetime_extension": 0.005, "dissolution": 0.0,
                     "pyrolysis": 0.005, "mechanical_recycling": 0.005,
                     "cement_co_processing": 0.005, "landfill": 0.98},
                 tpb_eol_coeff={'w_bi': 0.19, 'w_a': 0.29, 'w_sn': 0.19,
                                'w_pbc': -0.26, 'w_dpbc': -0.29, 'w_p': 0.04,
                                'w_b': -0.21},
                 attitude_eol_parameters={
                     "mean": 0.8, 'standard_deviation': 0.3, 'min': 0,
                     'max': 1},
                 choices_circularity={
                     "lifetime_extension": True, "dissolution": True,
                     "pyrolysis": True, "mechanical_recycling": True,
                     "cement_co_processing": True, "landfill": False,
                     "thermoset": False, "thermoplastic": True},
                 decommissioning_cost=[1300, 33000],
                 lifetime_extension_costs=[600, 6000],
                 rec_processes_costs={
                     "dissolution": [658, 659],
                     "pyrolysis": [285, 629],
                     "mechanical_recycling": [110, 310],
                     "cement_co_processing": [99, 132]},
                 transport_shreds={'shredding_costs': [99, 132],
                                   'transport_cost_shreds': [0.0314, 0.0820]},
                 transport_segments={
                     'cutting_costs': 27.56, 'transport_cost_segments': 8.7,
                     'length_segment': 30, 'segment_per_truck': 2},
                 transport_repair=1.57,
                 eol_pathways_transport_mode={
                     "lifetime_extension": 'transport_repair',
                     "dissolution": 'transport_segments',
                     "pyrolysis": 'transport_segments',
                     "mechanical_recycling": 'transport_segments',
                     "cement_co_processing": 'transport_segments',
                     "landfill": 'transport_segments'},
                 lifetime_extension_revenues=[124, 1.7E6],
                 rec_processes_revenues={
                     "dissolution": [658, 659], "pyrolysis": [332, 500],
                     "mechanical_recycling": [145, 292],
                     "cement_co_processing": [0, 1E-6]},
                 lifetime_extension_years=[5, 15],
                 le_feasibility=0.55,
                 early_failure_share=0.03,
                 blade_types={"thermoset": True, "thermoplastic": False},
                 blade_types_dist_init={"thermoset": 0.996,
                                        "thermoplastic": 0.004},
                 tpb_bt_coeff={'w_bi': 0.38, 'w_a': 0.30, 'w_sn': 0.21,
                               'w_pbc': -0.32, 'w_dpbc': -0.32, 'w_p': 0.00,
                               'w_b': 0.00},
                 attitude_bt_parameters={
                     'mean': 0.8, 'standard_deviation': 0.1, 'min': 0,
                     'max': 1},
                 blade_costs={"thermoset": [50E3, 500E3],
                              "thermoplastic_rate": [0.92, 1.04]},
                 recyclers_states={
                     "dissolution": [
                         "South Carolina", "Tennessee", "Iowa", "Texas",
                         "Florida", "Missouri"],
                     "pyrolysis": ["South Carolina", "Tennessee"],
                     "mechanical_recycling": ["Iowa", "Texas", "Florida"],
                     "cement_co_processing": ["Missouri"]},
                 learning_parameter={
                     "dissolution": [-0.21, -0.2],
                     "pyrolysis": [-0.21, -0.2],
                     "mechanical_recycling": [-0.21, -0.2],
                     "cement_co_processing": [-0.21, -0.2]},
                 blade_mass_fractions={
                     "steel": 0.05, "plastic": 0.09, "resin": 0.30,
                     "glass_fiber": 0.56},
                 rec_recovery_fractions={
                     "dissolution": {"steel": 1, "plastic": 1, "resin": 0.9,
                                     "glass_fiber": 0.5},
                     "pyrolysis": {"steel": 1, "plastic": 0, "resin": 0,
                                   "glass_fiber": 0.5},
                     "mechanical_recycling": {"steel": 1, "plastic": 1,
                                              "resin": 1, "glass_fiber": 1},
                     "cement_co_processing": {"steel": 1, "plastic": 0,
                                              "resin": 0, "glass_fiber": 1}},
                 bt_man_dist_init={"thermoset": 0.996, "thermoplastic": 0.004},
                 attitude_bt_man_parameters={
                     'mean': 0.9, 'standard_deviation': 0.1, 'min': 0,
                     'max': 1},
                 tpb_bt_man_coeff={'w_bi': 1.00, 'w_a': 0.15, 'w_sn': 0.125,
                                   'w_pbc': -0.24, 'w_dpbc': 0.00,
                                   'w_p': 0.00, 'w_b': 0.00},
                 lag_time_tp_blade_dev=5,
                 tp_production_share=1,
                 manufacturing_waste_ratio={
                     "steel": [0.12, 0.3], "plastic": [0.12, 0.3],
                     "resin": [0.12, 0.3], "glass_fiber": [0.12, 0.3]},
                 oem_states={
                     "wind_blade": [
                         "Colorado", "North Dakota", "South Dakota", "Iowa",
                         "Iowa"]},
                 man_waste_dist_init={
                     "dissolution": 0.0, "mechanical_recycling": 0.02,
                     "landfill": 0.98},
                 tpb_man_waste_coeff={
                     'w_bi': 0.19, 'w_a': 0.29, 'w_sn': 0.19, 'w_pbc': -0.26,
                     'w_dpbc': -0.29, 'w_p': 0.00, 'w_b': 0.00},
                 attitude_man_waste_parameters={
                     "mean": 0.5, 'standard_deviation': 0.1, 'min': 0,
                     'max': 1},
                 recycling_init_cap={
                     "dissolution": 1, "pyrolysis": 33100,
                     "mechanical_recycling": 54200,
                     "cement_co_processing": 54200},
                 conversion_factors={'metric_short_ton': 1.10231},
                 landfill_closure_threshold=[0.9, 1],
                 waste_volume_model={
                     'waste_volume': False, 'transport_segments': 0.034,
                     'transport_shreds': 0.33, 'transport_repair': np.nan,
                     'landfill_density': 1.009, 'cdw_density': 1.009,
                     'land_cost_conv': 0.47},
                 reg_landfill_threshold=[0.9, 1],
                 atb_land_wind={
                     'start': {'year': 2018, 't_cap': 2.4, 't_rd': 116},
                     'end': {'year': 2030, 't_cap': 5.5, 't_rd': 175}},
                 regulation_scenario={
                     'remaining_cap_based': False, 'empirically_based':
                         {'regulation': True, 'lag_time': [18, 32],
                          'regulation_freq': {
                              'ban_shreds': 0.23, 'ban_whole_only': 0.25,
                              'no_ban': 0.52}}},
                 recycler_margin={
                     "dissolution": [0.05, 0.25], "pyrolysis": [0.05, 0.25],
                     "mechanical_recycling": [0.05, 0.25],
                     "cement_co_processing": [0.05, 0.25]},
                 recyclers_names={
                     "dissolution": {
                         "South Carolina": 'Carbon Conversions - dissolution',
                         "Tennessee": 'Carbon Rivers - dissolution', "Iowa":
                             'GFS IA - dissolution', "Texas":
                             'GFS TX - dissolution', "Florida":
                             'EcoWolf - dissolution', "Missouri":
                             'Veolia - dissolution'}, "pyrolysis": {
                         "South Carolina": 'Carbon Conversions', "Tennessee":
                             'Carbon Rivers'}, "mechanical_recycling": {
                         "Iowa": 'GFS IA', "Texas": 'GFS TX', "Florida":
                             'EcoWolf'}, "cement_co_processing": {
                         "Missouri": 'Veolia'}},
                 detailed_transport_model=True
                 ):
        """
        Initiate model.
        :param seed: number used to initialize the random generator
        :param batch_run: enable varying different type of input parameters 
        (Mesa batch run inputs is limited to lists)
        :param manufacturers: number of manufacturers (man) for each 
        manufacturer type
        :param developers: number of developers (dev)
        :param recyclers: number of reyclers (rec) for each recycler type
        :param small_world_networks: characteristics of the small-world 
        networks representing social relationships within agent types (if 
        rewiring prob set to 0: regular lattice, if set to 1: random network)
        :param external_files: dictionary mapping files to their variables
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
        adoption in the wind plant owner (wpo) population
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
        :param bt_man_dist_init: initial distribution of blade types (bt) 
        design adoption within manufacturers
        :param attitude_bt_man_parameters: parameters for a truncated normal 
        distribution representing attitude among the population toward circular
        economy (CE) bt behaviors and to then infer non-circular behaviors
        :param tpb_bt_man_coeff: regression coefficient in the theory of 
        planned behavior (TPB) model of new blade design adoption
        :param lag_time_tp_blade_dev: number o years needed to develop
        thermoplastic blades
        :param tp_production_share: share of production assigned to 
        thermoplastic blades
        :param manufacturing_waste_ratio: manufacturing waste ratio for each
        material composing wind blades (percentage of finished blade mass)
        :param oem_states: state where the original equipment manufacturers 
        (oem) are located
        :param man_waste_dist_init: initial distribution of eol pathways 
        adoption in the manufacturers population
        :param tpb_man_waste_coeff: regression coefficient in the theory of 
        planned behavior (TPB) model of manufacturing waste management
        :param attitude_man_waste_parameters: parameters for a truncated 
        normal distribution representing attitude among the population 
        toward CE eol behaviors and then infer non-circular behaviors 
        for manufacturing waste
        :param recycling_init_cap: initial recycling capacity for each 
        recycling process (metric tons)
        :param  conversion_factors: dictionary of conversion factors
        :param landfill_closure_threshold: threshold value below which landfill
        closes (percentage of cumulative waste versus 2020 remaining capacity)
        :param waste_volume_model: dictionary containing conversion factors 
        to express waste in volume rather than mass unit (metric ton/m3)
        :param reg_landfill_threshold: percentage of landfill initial capacity 
        upon which regulator initiate a landfill ban
        :param atb_land_wind: annual technology baseline scenario for
        land wind reporting current and projected capacity and rotor diameter
        :param regulation_scenario: include regulator agents actions
        :param recycler_margin: margin of the minimum sustainable price
        :param recyclers_names: name of recycling companies
        """
        # Variables from inputs (value defined externally):
        self.seed = copy.deepcopy(seed)
        self.batch_run = copy.deepcopy(batch_run)
        self.calibration = calibration
        self.calibration_6 = calibration_6
        self.calibration_7 = calibration_7
        if self.batch_run:
            # TODO: below we use calibration variable for the SA on
            #  shredding costs - this should be removed eventually
            if calibration == 1:
                eol_pathways_transport_mode['pyrolysis'] = 'transport_shreds'
                eol_pathways_transport_mode['mechanical_recycling'] = \
                    'transport_shreds'
                eol_pathways_transport_mode['cement_co_processing'] = \
                    'transport_shreds'
                eol_pathways_transport_mode['landfill'] = 'transport_segments'
                transport_shreds['shredding_costs'] = [
                    calibration_2, 1E-6 + calibration_2]
                transport_shreds['transport_cost_shreds'] = [
                    calibration_3, 1E-6 + calibration_3]
            elif calibration == 2:
                eol_pathways_transport_mode['pyrolysis'] = 'transport_shreds'
                eol_pathways_transport_mode['mechanical_recycling'] = \
                    'transport_shreds'
                eol_pathways_transport_mode['cement_co_processing'] = \
                    'transport_shreds'
                if calibration_8 == 1:
                    eol_pathways_transport_mode['landfill'] = \
                        'transport_segments'
                else:
                    eol_pathways_transport_mode['landfill'] = \
                        'transport_shreds'
                # shred_cost_copy = copy.deepcopy(
                #    transport_shreds['shredding_costs'])
                transport_shreds['shredding_costs'] = [
                    transport_segments['cutting_costs'],
                    1E-6 + transport_segments['cutting_costs']]
                transport_shreds['transport_cost_shreds'] = [
                    transport_segments['transport_cost_segments'],
                    1E-6 + transport_segments['transport_cost_segments']]
                transport_shreds['shredding_costs'] = [
                    x * calibration_2 for x in
                    transport_shreds['shredding_costs']]
                transport_shreds['transport_cost_shreds'] = [
                    x * calibration_2 * 0.061 for x in
                    transport_shreds['transport_cost_shreds']]
                # rec_processes_revenues['pyrolysis'] = [
                #    x * (1 + calibration_8) for x in
                #    rec_processes_revenues['pyrolysis']]
                # red_cost = [x * (1 - self.calibration_2) for x in
                #            shred_cost_copy]
                # red_cost.sort(reverse=True)
                # for key, value in rec_processes_costs.items():
                #    reduced_costs = [
                #        x - y for x, y in zip(value, red_cost)]
                #    reduced_costs.sort()
                #    rec_processes_costs[key] = reduced_costs
                tpb_eol_coeff['w_b'] *= calibration_3
                tpb_eol_coeff['w_pbc'] *= calibration_4
                tpb_eol_coeff['w_sn'] *= calibration_5
                tpb_eol_coeff['w_a'] *= calibration_6
                tpb_eol_coeff['w_dpbc'] *= calibration_4
                tpb_eol_coeff['w_p'] *= calibration_7
            elif calibration == 3:
                attitude_eol_parameters["mean"] = calibration_2
                attitude_eol_parameters["standard_deviation"] = \
                    calibration_8
                tpb_eol_coeff['w_b'] = calibration_3
                tpb_eol_coeff['w_pbc'] = calibration_4
                tpb_eol_coeff['w_sn'] = calibration_5
                tpb_eol_coeff['w_a'] = calibration_6
                tpb_eol_coeff['w_bi'] = calibration_7
                # tpb_eol_coeff['w_p'] = calibration_8
            elif calibration == 4:
                eol_pathways_transport_mode['pyrolysis'] = 'transport_shreds'
                eol_pathways_transport_mode['mechanical_recycling'] = \
                    'transport_shreds'
                eol_pathways_transport_mode['cement_co_processing'] = \
                    'transport_shreds'
                eol_pathways_transport_mode['landfill'] = 'transport_segments'
                transport_shreds['shredding_costs'] = [
                    transport_segments['cutting_costs'],
                    1E-6 + transport_segments['cutting_costs']]
                transport_shreds['transport_cost_shreds'] = [
                    transport_segments['transport_cost_segments'],
                    1E-6 + transport_segments['transport_cost_segments']]
                transport_shreds['shredding_costs'] = [
                    x * calibration_2 for x in
                    transport_shreds['shredding_costs']]
                transport_shreds['transport_cost_shreds'] = [
                    x * calibration_3 * 0.061 for x in
                    transport_shreds['transport_cost_shreds']]
                tpb_eol_coeff['w_b'] *= calibration_4
            elif calibration == 5:
                eol_pathways_transport_mode['pyrolysis'] = 'transport_shreds'
                eol_pathways_transport_mode['mechanical_recycling'] = \
                    'transport_shreds'
                eol_pathways_transport_mode['cement_co_processing'] = \
                    'transport_shreds'
                eol_pathways_transport_mode['landfill'] = 'transport_segments'
                transport_shreds['shredding_costs'] = [
                    calibration_2, 1E-6 + calibration_2]
                transport_shreds['transport_cost_shreds'] = [
                    calibration_3, 1E-6 + calibration_3]
                tpb_eol_coeff['w_b'] *= calibration_8
            elif calibration == 6:
                attitude_bt_parameters['mean'] = calibration_2
                attitude_bt_man_parameters['mean'] = calibration_3
                rec_processes_revenues['dissolution'] = [
                    calibration_4, 1E-6 + calibration_4]
            elif calibration == 7:
                eol_pathways_transport_mode['pyrolysis'] = 'transport_shreds'
                eol_pathways_transport_mode['mechanical_recycling'] = \
                    'transport_shreds'
                eol_pathways_transport_mode['cement_co_processing'] = \
                    'transport_shreds'
                if calibration_4 == 1:
                    eol_pathways_transport_mode['landfill'] = \
                        'transport_shreds'
                else:
                    eol_pathways_transport_mode['landfill'] = \
                        'transport_segments'
                tpb_eol_coeff['w_a'] *= calibration_5
                tpb_eol_coeff['w_sn'] *= calibration_5
                tpb_eol_coeff['w_b'] *= calibration_5
                tpb_eol_coeff['w_p'] *= calibration_5
            elif calibration == 8:
                attitude_bt_parameters['mean'] = calibration_2
                attitude_bt_man_parameters['mean'] = calibration_3
                rec_processes_revenues['dissolution'] = [
                    calibration_4, 1E-6 + calibration_4]
                blade_types = {"thermoset": True, "thermoplastic": True}
            elif calibration == 9:
                if calibration_3 == 1:
                    eol_pathways_transport_mode['pyrolysis'] = \
                        'transport_segments'
                    eol_pathways_transport_mode['mechanical_recycling'] = \
                        'transport_segments'
                    eol_pathways_transport_mode['cement_co_processing'] = \
                        'transport_shreds'
                    eol_pathways_transport_mode['landfill'] = \
                        'transport_segments'
                    transport_shreds['shredding_costs'] = [
                        transport_segments['cutting_costs'],
                        1E-6 + transport_segments['cutting_costs']]
                    transport_shreds['transport_cost_shreds'] = [
                        transport_segments['transport_cost_segments'],
                        1E-6 + transport_segments['transport_cost_segments']]
                    transport_shreds['shredding_costs'] = [
                        x * calibration_2 for x in
                        transport_shreds['shredding_costs']]
                    transport_shreds['transport_cost_shreds'] = [
                        x * calibration_2 * 0.061 for x in
                        transport_shreds['transport_cost_shreds']]
                rec_processes_costs['cement_co_processing'] = [
                    99 * calibration_2, 132 * calibration_2]
                rec_processes_revenues['cement_co_processing'] = [1E-5, 1E-4]
                eol_pathways_dist_init = {
                    "lifetime_extension": 0.005, "dissolution": 0,
                    "pyrolysis": 0.005, "mechanical_recycling": 0.005,
                    "cement_co_processing": 0.005 + calibration_5,
                    "landfill": 0.98 - calibration_5}
                tpb_eol_coeff['w_sn'] = calibration_6
                # tpb_eol_coeff['w_b'] *= calibration_7
            elif calibration == 10:
                if calibration_2 == 0:
                    eol_pathways = {
                        "lifetime_extension": False, "dissolution": False,
                        "pyrolysis": True, "mechanical_recycling": True,
                        "cement_co_processing": True, "landfill": True}
            elif calibration == 11:
                if calibration_5 == 1:
                    attitude_bt_parameters['mean'] = calibration_2
                    attitude_bt_man_parameters['mean'] = calibration_3
                    rec_processes_revenues['dissolution'] = [
                        calibration_4, 1E-6 + calibration_4]
                    blade_types = {"thermoset": True, "thermoplastic": True}
                if calibration_6 == 1:
                    recyclers = {
                        "dissolution": 6, "pyrolysis": 4,
                        "mechanical_recycling": 6, "cement_co_processing": 2}
                    additional_locations = {
                        'Texas': "City of Robert Lee Landfill",
                        'Illinois': "Brickyard Disposal & Recycling Inc",
                        'California': "Tehachapi Sanitary Landfill",
                        'Pennsylvania': "Alliance Sanitary Landfill, Inc.",
                        'Iowa': "Northwest Iowa Area Solid Waste Agency",
                        'New York': "Clinton County Landfill / Schuyler Falls"}
                    recyclers_names = {
                        "dissolution": {
                            "South Carolina":
                                ['Carbon Conversions - dissolution'],
                            "Tennessee": ['Carbon Rivers - dissolution'],
                            "Iowa": ['GFS IA - dissolution'], "Texas":
                                ['GFS TX - dissolution'], "Florida":
                                ['EcoWolf - dissolution'], "Missouri":
                                ['Veolia - dissolution']},
                        "pyrolysis": {
                            "South Carolina": ['Carbon Conversions'],
                            "Tennessee":
                                ['Carbon Rivers']}, "mechanical_recycling": {
                            "Iowa": ['GFS IA'], "Texas": ['GFS TX'], "Florida":
                                ['EcoWolf']}, "cement_co_processing": {
                            "Missouri": ['Veolia']}}
                    list_add_loc = list(additional_locations.items())
                    random.shuffle(list_add_loc)
                    # noinspection PyTypeChecker
                    additional_locations = dict(list_add_loc)
                    for rec_type in recyclers_states.keys():
                        if rec_type != "dissolution":
                            for iteration in range(
                                    int(recyclers[rec_type] / 2)):
                                add_state_list = \
                                    list(additional_locations.keys())
                                add_name_list = \
                                    list(additional_locations.values())
                                added_name = add_name_list.pop()
                                added_state = add_state_list.pop()
                                additional_locations.pop(added_state)
                                new_state_list = recyclers_states[rec_type]
                                new_state_list.append(added_state)
                                recyclers_states[rec_type] = new_state_list
                                if added_state in recyclers_names[rec_type]:
                                    new_name_list = \
                                        recyclers_names[rec_type][added_state]
                                    new_name_list.append(added_name)
                                    recyclers_names[rec_type][added_state] = \
                                        new_name_list
                                else:
                                    recyclers_names[rec_type][added_state] = \
                                        [added_name]
                elif calibration_6 == 2:
                    recyclers_names = {
                        "dissolution": {
                            "South Carolina": 'City of Robert Lee Landfill',
                            "Tennessee": 'Brickyard Disposal & Recycling Inc',
                            "Iowa":
                                'Tehachapi Sanitary Landfill', "Texas":
                                'Alliance Sanitary Landfill, Inc.',
                            "Florida":
                                'Northwest Iowa Area Solid Waste Agency',
                            "Missouri":
                                'Clinton County Landfill / Schuyler Falls'},
                        "pyrolysis": {
                            "South Carolina": 'Carbon Conversions',
                            "Tennessee":
                                'Carbon Rivers'}, "mechanical_recycling": {
                            "Iowa": 'GFS IA', "Texas": 'GFS TX', "Florida":
                                'EcoWolf'}, "cement_co_processing": {
                            "Missouri": 'Veolia'}}
                tpb_eol_coeff['w_b'] *= calibration_7
            elif calibration == 12:
                eol_pathways_transport_mode['pyrolysis'] = 'transport_shreds'
                eol_pathways_transport_mode['mechanical_recycling'] = \
                    'transport_shreds'
                eol_pathways_transport_mode['cement_co_processing'] = \
                    'transport_shreds'
                eol_pathways_transport_mode['landfill'] = 'transport_segments'
                transport_shreds['shredding_costs'] = [
                    transport_segments['cutting_costs'],
                    1E-6 + transport_segments['cutting_costs']]
                transport_shreds['transport_cost_shreds'] = [
                    transport_segments['transport_cost_segments'],
                    1E-6 + transport_segments['transport_cost_segments']]
                transport_shreds['shredding_costs'] = [
                    x * calibration_2 for x in
                    transport_shreds['shredding_costs']]
                transport_shreds['transport_cost_shreds'] = [
                    x * calibration_2 * 0.061 for x in
                    transport_shreds['transport_cost_shreds']]
                if calibration_3 == 0:
                    detailed_transport_model = False
                tpb_eol_coeff['w_b'] *= calibration_4
                tpb_eol_coeff['w_sn'] *= calibration_5
            elif calibration == 13:
                attitude_bt_parameters['mean'] = calibration_9
            else:
                pass
        # TODO: above we use calibration variable for the SA on
        #  shredding costs - this should be removed eventually
        random.seed(self.seed)
        self.manufacturers = copy.deepcopy(manufacturers)
        self.developers = copy.deepcopy(developers)
        self.recyclers = copy.deepcopy(recyclers)
        self.small_world_networks = copy.deepcopy(small_world_networks)
        self.external_files = copy.deepcopy(external_files)
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
        self.bt_man_dist_init = copy.deepcopy(bt_man_dist_init)
        self.attitude_bt_man_parameters = copy.deepcopy(
            attitude_bt_man_parameters)
        self.tpb_bt_man_coeff = copy.deepcopy(tpb_bt_man_coeff)
        self.lag_time_tp_blade_dev = copy.deepcopy(lag_time_tp_blade_dev)
        self.tp_production_share = copy.deepcopy(tp_production_share)
        self.manufacturing_waste_ratio = copy.deepcopy(
            manufacturing_waste_ratio)
        self.oem_states = copy.deepcopy(oem_states)
        self.tpb_man_waste_coeff = copy.deepcopy(tpb_man_waste_coeff)
        self.man_waste_dist_init = copy.deepcopy(man_waste_dist_init)
        self.attitude_man_waste_parameters = copy.deepcopy(
            attitude_man_waste_parameters)
        self.recycling_init_cap = copy.deepcopy(recycling_init_cap)
        self.conversion_factors = copy.deepcopy(conversion_factors)
        self.landfill_closure_threshold = copy.deepcopy(
            landfill_closure_threshold)
        self.waste_volume_model = copy.deepcopy(waste_volume_model)
        self.reg_landfill_threshold = copy.deepcopy(reg_landfill_threshold)
        self.atb_land_wind = copy.deepcopy(atb_land_wind)
        self.regulation_scenario = copy.deepcopy(regulation_scenario)
        self.recycler_margin = copy.deepcopy(recycler_margin)
        self.recyclers_names = copy.deepcopy(recyclers_names)
        self.detailed_transport_model = copy.deepcopy(detailed_transport_model)
        # Internal variables:
        self.running = True  # required for batch runs
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
        self.wbj_database = self.landfill_data(
            self.external_files["wbj_database"], self.state_abrev,
            self.temporal_scope, self.conversion_factors['metric_short_ton'],
            self.waste_volume_model)
        self.cap_projections = \
            pd.read_csv(self.external_files["projections"])
        self.growth_rates = self.compute_growth_rates(
            self.uswtdb, self.cap_projections, self.temporal_scope,
            self.compound_annual_growth_rate)
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
            self.remove_item_dic_from_boolean_dic(
                self.eol_pathways_dist_init.copy(), self.eol_pathways),
            self.uswtdb.shape[0], True, [])
        self.list_init_eol_second_choice = self.list_init_eol_pathways.copy()
        self.list_init_blade_types = self.roulette_wheel_choice(
            self.remove_item_dic_from_boolean_dic(
                self.blade_types_dist_init.copy(), self.blade_types),
            sum(self.developers.values()), True, [])
        self.list_init_bt_second_choice = self.list_init_blade_types.copy()
        self.list_bt_man = self.roulette_wheel_choice(
            self.remove_item_dic_from_boolean_dic(
                self.bt_man_dist_init.copy(), self.blade_types),
            self.manufacturers['wind_blade'], True, [])
        self.list_bt_man_second_choice = self.list_bt_man.copy()
        self.list_add_agent_eol_path = []
        self.eol_pathway_dist_list = []
        self.eol_pathway_dist_dic = {}
        self.states_waste_eol_path = self.nested_init_dic(
            0, self.growth_rates.keys(), self.eol_pathways.keys())
        self.variables_recyclers = self.initial_dic_from_key_list(
            self.recyclers.keys(), [])
        self.variables_recyclers_tr = self.initial_dic_from_key_list(
            self.recyclers.keys(), [])
        self.variables_landfills = self.initial_dic_from_key_list(
            self.wbj_database['landfill_type'].unique().tolist(), [])
        self.variables_landfills_tr = self.initial_dic_from_key_list(
            self.wbj_database['landfill_type'].unique().tolist(), [])
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
        self.rec_land_volume = {}
        self.average_eol_costs = self.initial_dic_from_key_list(
            self.eol_pathways.keys(), 0)
        self.recovered_materials = self.initial_dic_from_key_list(
            self.blade_mass_fractions.keys(), 0)
        self.bt_manufactured_q = self.initial_dic_from_key_list(
            self.blade_types.keys(), 0)
        self.manufacturing_waste_q = self.nested_init_dic(
            0, self.eol_pathways, self.manufacturing_waste_ratio.keys())
        self.weighted_avr_mass_conv_factor = 0
        self.add_state_projections = \
            self.cap_projections.loc[
                self.cap_projections['start_year'] >
                self.temporal_scope['simulation_start']].\
            set_index('state').to_dict('index')
        self.list_man_waste = self.roulette_wheel_choice(
            self.remove_item_dic_from_boolean_dic(
                self.man_waste_dist_init.copy(), self.eol_pathways),
            self.manufacturers['wind_blade'], True, [])
        self.list_tb_lifetimes = []
        self.average_lifetimes_wpo = []
        self.total_eol_costs = self.nested_init_dic(
            0, self.growth_rates.keys(), self.eol_pathways.keys())
        self.total_eol_revenues = self.nested_init_dic(
            0, self.growth_rates.keys(), self.eol_pathways.keys())
        self.total_man_waste_costs = self.initial_dic_from_key_list(
            self.eol_pathways.keys(), 0)
        self.total_man_waste_revenues = self.initial_dic_from_key_list(
            self.eol_pathways.keys(), 0)
        self.total_bt_costs = self.initial_dic_from_key_list(
            self.blade_types.keys(), 0)
        self.blade_type_mass = self.initial_dic_from_key_list(
            self.blade_types.keys(), 0)
        self.landfill_remaining_cap = self.initial_dic_from_key_list(
            self.growth_rates.keys(), 0)
        self.init_land_capacity = self.initial_dic_from_key_list(
            self.growth_rates.keys(), 0)
        self.state_blade_waste = self.initial_dic_from_key_list(
            self.growth_rates.keys(), 0)
        self.yearly_waste_ratios = self.nested_init_dic(
            0, list(range(self.temporal_scope['simulation_start'],
                          self.temporal_scope['simulation_end'])),
            self.eol_pathways)
        self.past_eol_waste = self.initial_dic_from_key_list(
            self.eol_pathways, 0)
        self.landfill_count = 0
        self.empirical_regulations = self.roulette_wheel_choice(
            self.regulation_scenario['empirically_based']['regulation_freq'],
            self.regulators, False, [])
        self.transport_shreds_mandate = self.nested_init_dic(
            False, self.choices_circularity.keys(), self.growth_rates.keys())
        self.cum_blade_ratios = self.nested_init_dic(
            0, list(range(self.temporal_scope['simulation_start'],
                          self.temporal_scope['simulation_end'])),
            self.blade_types)
        self.cum_waste_ratios = self.nested_init_dic(
            0, list(range(self.temporal_scope['simulation_start'],
                          self.temporal_scope['simulation_end'])),
            self.eol_pathways)
        # Computing transportation distances:
        if self.detailed_transport_model:
            self.all_shortest_paths_or_trg = pd.read_csv(
                self.external_files["detailed_distances"], index_col=0,
                header=0)
        else:
            self.all_shortest_paths_or_trg = pd.read_csv(
                self.external_files["state_distances"], index_col=0)
        self.all_shortest_paths_or_trg_default = pd.read_csv(
            self.external_files["state_distances"], index_col=0)
        # Creating agents and social networks:
        self.schedule = BaseScheduler(self)
        self.G_rec, self.grid_rec, self.schedule_rec = \
            self.network_grid_schedule_agents(
                sum(self.recyclers.values()),
                self.small_world_networks["recyclers"]["node_degree"],
                self.small_world_networks["recyclers"]["rewiring_prob"],
                sum(self.recyclers.values()), Recycler)
        self.first_land_id = self.unique_id
        self.G_land, self.grid_land, self.schedule_land = \
            self.network_grid_schedule_agents(
                self.wbj_database.shape[0],
                self.small_world_networks["landfills"]["node_degree"],
                self.small_world_networks["landfills"]["rewiring_prob"],
                self.wbj_database.shape[0], Landfill)
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
                    (self.p_install_growth +
                     len(self.add_state_projections))),
                self.small_world_networks[
                    "wind_plant_owners"]["node_degree"],
                self.small_world_networks[
                    "wind_plant_owners"]["rewiring_prob"],
                self.uswtdb.shape[0], WindPlantOwner)
        self.grid_oem = self.create_subset_grid(
            self.schedule_man, self.manufacturers['wind_blade'],
            self.small_world_networks['original_equipment_manufacturer'][
                'node_degree'], self.small_world_networks[
                'original_equipment_manufacturer']['rewiring_prob'], self.seed,
            'manufacturer_type', 'wind_blade')
        self.additional_id = self.first_wpo_id + self.uswtdb.shape[0]
        # Create data collectors:
        self.model_reporters = {
            "Year": lambda a:
            self.clock + self.temporal_scope['simulation_start'] - 1,
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
                lambda a: str(self.average_eol_costs),
            "Recovered materials (metric tons)":
                lambda a: str(self.recovered_materials),
            "Manufactured blades (MW)":
                lambda a: str(self.bt_manufactured_q),
            "Manufacturing waste (metric tons)":
                lambda a: str(self.manufacturing_waste_q),
            "Turbines average lifetime (years)":
                lambda a: self.safe_div(sum(self.average_lifetimes_wpo),
                                        len(self.average_lifetimes_wpo)),
            "Total eol costs ($)":
                lambda a: str(self.total_eol_costs),
            "Total eol revenues ($)":
                lambda a: str(self.total_eol_revenues),
            "Total manufacturing waste costs ($)":
                lambda a: str(self.total_man_waste_costs),
            "Total manufacturing waste revenues ($)":
                lambda a: str(self.total_man_waste_revenues),
            "Total blade costs ($)":
                lambda a: str(self.total_bt_costs),
            "Landfill waste volume model": lambda a: self.waste_volume_model[
                'waste_volume'],
            "Landfill number": lambda a: self.landfill_count,
            "Landfills remaining capacity (ton or m3)":
                lambda a: str(self.landfill_remaining_cap),
            "Landfills initial capacity (ton or m3)":
                lambda a: str(self.init_land_capacity),
            "Landfill ban enacted":
                lambda a: str({key: value['landfill'] for key, value in
                               self.bans_enacted.items()}),
            "Blade waste in landfill":
                lambda a: str(self.state_blade_waste),
            "Yearly waste ratios":
                lambda a: str(self.yearly_waste_ratios),
            "Cumulative blade ratios":
                lambda a: str(self.cum_blade_ratios),
            "Cumulative waste ratios":
                lambda a: str(self.cum_waste_ratios)}
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
        social_network = nx.watts_strogatz_graph(
            nodes, node_degree, rewiring_prob, seed=random.seed(seed))
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

    def adding_state_w_cap(self, scenario, temporal_scope, clock, grid,
                           schedule, agent_type):
        """
        Add agents (wind plant projects) from states which were not in the
        uswtdb according to projection scenarios
        :param scenario: projection scenario (e.g., standard scenarios)
        :param temporal_scope: temporal scope of the simulation
        :param clock: model clock
        :param grid: the network relating the agents
        :param schedule: the schedule of the agent type
        :param agent_type: the agent type
        """
        for key, value in scenario.items():
            if (value['start_year'] - 1) == \
                    (temporal_scope['simulation_start'] + clock) and \
                    value['start_year'] != temporal_scope['simulation_start']:
                a = agent_type(
                    self.additional_id, self, new_p_state=key,
                    new_p_cap=value['start_cap'])
                schedule.add(a)
                grid.place_agent(
                    a, (self.additional_id - self.first_wpo_id))
                self.schedule.add(a)
                self.additional_id += 1

    @staticmethod
    def compute_growth_rates(uswtdb, projections, temporal_scope,
                             growth_rate_formula):
        """
        Compute growth rates used in the compounded annual growth function
        :param uswtdb: us wind turbine database
        :param projections: projected quantities at years x, y for each state
        :param temporal_scope: temporal scope of the simulation
        :param growth_rate_formula: compound annual growth rate function
        :return: growth rates (by states)
        """
        growth_rates = {}
        projections_dict = projections.set_index('state').to_dict('index')
        for key, value in projections_dict.items():
            if value['start_year'] == temporal_scope['simulation_start']:
                uswtdb_state_cap = uswtdb.groupby(['t_state']).sum()
                uswtdb_state_cap = uswtdb_state_cap.loc[key]
                start_cap = float(uswtdb_state_cap['p_cap'])
            else:
                start_cap = value['start_cap']
            end_cap = value['2050_cap']
            end_year = value['end_year']
            start_year = value['start_year']
            state_growth_rate = growth_rate_formula(
                end_cap, start_cap, end_year, start_year)
            growth_rates[key] = state_growth_rate
        return growth_rates

    @staticmethod
    def compound_annual_growth_rate(end_value, start_value, end_year,
                                    start_year):
        """
        Compound_annual_growth_rate formula
        :param end_value: value after growth
        :param start_value: value before growth
        :param end_year: year after growth
        :param start_year: year before growth
        :return: growth rate
        """
        number_year = end_year - start_year
        growth_rate = (end_value / start_value)**(1 / number_year) - 1
        return growth_rate

    def create_subset_grid(self, schedule, nodes, node_degree, rewiring_prob,
                           seed, attribute, condition):
        """
        Create a subset grid from a given schedule of agents
        :param schedule: Mesa scheduler of the agent type
        :param nodes: number of nodes in the graph
        :param node_degree: node degree of the equivalent regular lattice
        :param rewiring_prob: probability of rewiring a given edge
        :param seed: random seed for the small-world network
        :param attribute: attribute to select agents to build a subset grid for
        :param condition: condition of the attribute agents must have to be
        part of the subset grid
        :return: the subset grid
        """
        new_graph = self.creating_social_network(
            nodes, node_degree, rewiring_prob, seed)
        new_grid = NetworkGrid(new_graph)
        agents_to_add = []
        for agent in schedule.agents:
            variable_of_interest = getattr(agent, attribute)
            if variable_of_interest == condition:
                agents_to_add.append(agent)
        for node in new_graph:
            new_grid.place_agent(agents_to_add.pop(), node)
        return new_grid

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
        uswtdb = uswtdb.groupby(['p_name']).agg(
            lambda x: x.head(1) if x.dtype == 'object' else
            x.mean()).reset_index()
        uswtdb = uswtdb[['p_name', 'p_year', 'p_tnum', 't_state', 't_rd',
                         't_cap', 'xlong', 'ylat']]
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
    def landfill_data(database, state_abrev, temporal_scope, metric_short_ton,
                      waste_volume_model):
        if waste_volume_model['waste_volume']:
            m_v_conv_factor_land = waste_volume_model['landfill_density']
            m_v_conv_factor_cdw = waste_volume_model['cdw_density']
        else:
            m_v_conv_factor_land = 1
            m_v_conv_factor_cdw = 1
        wbj_database = pd.read_csv(database, thousands=',')
        wbj_database = wbj_database[
            ['Facility Name', 'State', 'Longitude', 'Latitude', 'Start Date',
             'Close Date', 'Waste Types Accepted', '$/ Ton',
             'Remaining Capacity (tons)', 'Total Waste in 2020_tons']]
        wbj_database['Remaining Capacity (tons)'] = wbj_database[
            'Remaining Capacity (tons)'].astype(float) * metric_short_ton \
            / m_v_conv_factor_land
        wbj_database['Total Waste in 2020_tons'] = wbj_database[
            'Total Waste in 2020_tons'].astype(float) * metric_short_ton \
            / m_v_conv_factor_cdw
        wbj_database = wbj_database[
            wbj_database['Remaining Capacity (tons)'] > 0]
        wbj_database['Close Date'] = pd.DatetimeIndex(
            wbj_database['Close Date'].astype('datetime64')).year
        wbj_database['Close Date'] = wbj_database['Close Date'].fillna(2050)
        wbj_database['Start Date'] = pd.DatetimeIndex(
            wbj_database['Start Date'].astype('datetime64')).year
        wbj_database = wbj_database[wbj_database['Close Date'] >
                                    temporal_scope['simulation_start']]
        wbj_database['current_date'] = temporal_scope['simulation_start']
        wbj_database['years_opened'] = wbj_database['current_date'] - \
            wbj_database['Start Date']
        # assumes that waste in 2020 is a typical year
        wbj_database['yearly_waste'] = wbj_database['Total Waste in 2020_tons']
        wbj_database['accept_blade_waste'] = wbj_database[
            'Waste Types Accepted'].str.find('C&D Waste' or 'Indust. Waste')
        # by default, consider wind blades as C&D waste
        wbj_database = wbj_database[wbj_database['accept_blade_waste'] >= 0]
        wbj_database = wbj_database[(wbj_database['State'] != 'AK') &
                                    (wbj_database['State'] != 'HI')]
        wbj_database['landfill_type'] = 'landfill'
        wbj_database = wbj_database.replace({'State': state_abrev})
        wbj_database = wbj_database.dropna()
        wbj_database = wbj_database.reset_index(drop=True)
        return wbj_database

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
        :param deterministic: if False randomly select the pick (where the ball
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
            if not value and key in dic:
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

    def pressure(self, state, regulations, choices_circularity):
        """
        Computes the TPB pressure scores for each circular and non-circular
        choices as measured by the weighted (by the distance to the agent)
        average of states that have enacted some regulations
        :param state: state of the agent
        :param regulations: a nested dictionary of choices and states that
        containing Booleans with True when the regulator in the state has
        enacted regulation(s) for the given choice and False otherwise
        :param choices_circularity: dictionary qualifying choices in terms of
        circularity, this may affect agents decision (e.g., agents may hold a
        different attitude depending on the choice circularity
        :return: the pressure scores for each choice
        """
        scores = {}
        all_or_trg_distances = self.all_shortest_paths_or_trg_default[state]
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
            if choices_circularity[key]:
                scores[key] = weighted_sum / pressure_max
            else:
                scores[key] = -1 * weighted_sum / pressure_max
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
        scores_sn = self.divide_value_by_tot_dic(
            self.subjective_norms(grid, adopted_choice, position, dic_choices))
        scores_a = self.divide_value_by_tot_dic(
            self.attitude(ce_att_level, conv_att_level, dic_choices,
                          choices_circularity))
        scores_pbc = self.divide_value_by_tot_dic(
            self.perceived_behavioral_control_and_barrier(cost_choices))
        scores_b = self.divide_value_by_tot_dic(
            self.perceived_behavioral_control_and_barrier(barrier_choices))
        # TODO code changed for Figure 3
        if self.calibration == 9 and 'cement_co_processing' in scores_b:
            scores_b['cement_co_processing'] = self.calibration_7
        # TODO code changed for Figure 3
        scores_p = self.divide_value_by_tot_dic(
            self.pressure(state, regulations, choices_circularity))
        scores_behaviors = self.total_tpb_scores(
            dic_choices, tpb_weights, scores_sn, scores_a, scores_pbc,
            scores_b, scores_p)
        first_choice = self.select_highest_scores_in_dic(
            scores_behaviors, np.nan, True)
        dic_second_choices = dic_choices.copy()
        dic_second_choices.pop(first_choice)
        scores_sn.pop(first_choice)
        scores_sn = self.divide_value_by_tot_dic(scores_sn)
        scores_a.pop(first_choice)
        scores_a = self.divide_value_by_tot_dic(scores_a)
        scores_pbc.pop(first_choice)
        scores_pbc = self.divide_value_by_tot_dic(scores_pbc)
        scores_b.pop(first_choice)
        scores_b = self.divide_value_by_tot_dic(scores_b)
        scores_p.pop(first_choice)
        scores_p = self.divide_value_by_tot_dic(scores_p)
        scores_behaviors = self.total_tpb_scores(
            dic_second_choices, tpb_weights, scores_sn, scores_a, scores_pbc,
            scores_b, scores_p)
        second_choice = self.select_highest_scores_in_dic(
            scores_behaviors, first_choice, False)
        return first_choice, second_choice

    @staticmethod
    def total_tpb_scores(dic_choices, tpb_weights, scores_sn, scores_a,
                         scores_pbc, scores_b, scores_p):
        scores_behaviors = {}
        for key, value in dic_choices.items():
            scores_behaviors[key] = tpb_weights['w_bi'] * (
                    tpb_weights['w_sn'] * scores_sn[key] +
                    tpb_weights['w_a'] * scores_a[key] +
                    tpb_weights['w_pbc'] * scores_pbc[key]) + \
                    tpb_weights['w_dpbc'] * scores_pbc[key] + \
                    tpb_weights['w_b'] * scores_b[key] + \
                    tpb_weights['w_p'] * scores_p[key]
            if not value:
                scores_behaviors.pop(key)
        return scores_behaviors

    @staticmethod
    def select_highest_scores_in_dic(dic, first_choice, first):
        choices = [keys for keys, values in dic.items() if
                   values == max(dic.values())]
        # if two behavior equally score the highest, choose randomly
        random.shuffle(choices)
        if choices or first:
            if choices:
                selected_choice = choices[0]
            # due to landfill ban no first choice can be available to
            # manufacturer if no recycling option is available. In that case,
            # force landfill to avoid errors
            else:
                selected_choice = 'landfill'
        # if no other choice than lifetime_extension is available, forces the
        # blade to landfill as otherwise they would not get in any EOL pathway
        # and generate errors
        elif first_choice != 'lifetime_extension':
            selected_choice = first_choice
        else:
            selected_choice = 'landfill'
        return selected_choice

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

    # TODO: write unittest
    @staticmethod
    def learning_effect(original_volume, volume, original_cost,
                        current_cost, learning_parameter, learning_function):
        """
        Model the learning effect from recycler: as the quantity of blades
        sent to recyclers increases, the recyclers can lower their processes'
        costs, e.g., due to economies of scale and technological advancement;
        cost can only decreased, if recycled quantity decreases, the recycling
        cost remain the same as its current value
        :param original_volume: the original quantity of blades recycled
        (at the beginning of the simulation)
        :param volume: the volume of blade recycled currently (at the current
        time step)
        :param original_cost: the initial recycling cost (at the beginning of
        the simulation)
        :param current_cost: the current recycling cost
        :param learning_parameter: parameter of the learning function used to
        model the learning effect
        :param learning_function: function to compute the decreased in costs
        due to economies of scales and other learning effects
        :return: the current recycling cost
        """
        if volume > 0:
            decreased_cost = learning_function(
                original_volume, volume, original_cost, learning_parameter)
            if decreased_cost < current_cost:
                cost = decreased_cost
            else:
                cost = current_cost
        else:
            cost = current_cost
        return cost

    # TODO: write unittest
    @staticmethod
    def learning_function(original_volume, volume, original_cost,
                          learning_parameter):
        """
        The learning function used to model the learning effect
        :param original_volume: the original quantity of blades recycled
        (at the beginning of the simulation)
        :param volume: the volume of blade recycled currently (at the current
        time step)
        :param original_cost: the initial recycling cost (at the beginning of
        the simulation)
        :param learning_parameter: parameter of the learning function used to
        model the learning effect
        :return: the decreased costs due to the learning effect
        """
        decreased_cost = original_cost * \
            (volume / original_volume)**learning_parameter
        return decreased_cost

    # TODO: write unittest
    @staticmethod
    def costs_eol_pathways(
            eol_tr_costs_shreds, eol_tr_costs_segments, eol_tr_costs_repair,
            variables_recyclers, variables_landfills, variables_developers,
            decommissioning_cost, eol_pathways, transport_mode_model,
            minimum_tr_proc_costs, eol_unique_ids_selected,
            convert_unit_land_cost, waste_volume_model,
            transport_shreds_mandate, state):
        """
        Compute costs for each eol pathway accounting for decommissioning costs
        (similar for each eol pathway), transportation costs (including
        pre-processing (shredding or cutting), and eol net costs (costs minus
        potential revenue)
        :param eol_tr_costs_shreds: transportation after shredding costs
        :param eol_tr_costs_segments: transportation after cutting costs
        :param eol_tr_costs_repair: transportation costs for repair
        :param variables_recyclers: unique_id, location, process cost
        :param variables_landfills: unique_id, location, landfill cost
        :param variables_developers: unique_id, transportation cost, process
        cost
        :param decommissioning_cost: decommissioning cost, similar for all eol
        pathway
        :param eol_pathways: different choices of eol pathways
        :param transport_mode_model: model for transportation mode (process and
        transport costs)
        :param minimum_tr_proc_costs: function to compute minimum total
        (transport and process) costs
        :param eol_unique_ids_selected: report the unique_ids of selected
        agents for each eol pathways
        :param convert_unit_land_cost: function to convert landfill costs
        :param waste_volume_model: model to convert volumes in tons to volumes
        in m3 according to the state of the EOL blades (shreds or segments)
        :param transport_shreds_mandate: force transport mode to be in shreds
        form as some regulation (e.g., of landfills) may require shreds form
        :param state: wpo location state
        :return: costs for each eol pathway
        """
        costs_eol_pathways = {}
        rev_eol_pathways = {}
        process_costs = {}
        eol_path_transport = {}
        process_costs.update(variables_landfills)
        process_costs.update(variables_recyclers)
        process_costs.update(variables_developers)
        for key in eol_pathways.keys():
            if transport_shreds_mandate[key][state]:
                transport_mode = "transport_shreds"
            else:
                transport_mode = transport_mode_model[key]
            if transport_mode == "transport_shreds":
                transport_cost = eol_tr_costs_shreds[key]
                process_costs_key = convert_unit_land_cost(
                    waste_volume_model, key, process_costs, transport_mode)
                opt_costs = minimum_tr_proc_costs(
                    process_costs_key, transport_cost)
                tr_proc_costs = opt_costs[0]
                revenue = opt_costs[1]
            elif transport_mode == "transport_segments":
                transport_cost = eol_tr_costs_segments[key]
                process_costs_key = convert_unit_land_cost(
                    waste_volume_model, key, process_costs, transport_mode)
                opt_costs = minimum_tr_proc_costs(
                    process_costs_key, transport_cost)
                tr_proc_costs = opt_costs[0]
                revenue = opt_costs[1]
            elif transport_mode == "transport_repair":
                transport_cost = eol_tr_costs_repair[key]
                process_costs_key = process_costs[key]
                opt_costs = minimum_tr_proc_costs(
                    process_costs_key, transport_cost)
                tr_proc_costs = opt_costs[0]
                revenue = opt_costs[1]
            else:
                process_costs_key_shreds = convert_unit_land_cost(
                    waste_volume_model, key, process_costs, 'transport_shreds')
                process_costs_key_segments = convert_unit_land_cost(
                    waste_volume_model, key, process_costs,
                    'transport_segments')
                transport_cost_shreds = eol_tr_costs_shreds[key]
                opt_costs_shreds = minimum_tr_proc_costs(
                    process_costs_key_shreds, transport_cost_shreds)
                tr_proc_costs_shreds = opt_costs_shreds[0]
                transport_cost_segments = eol_tr_costs_segments[key]
                opt_costs_segments = minimum_tr_proc_costs(
                    process_costs_key_segments, transport_cost_segments)
                tr_proc_costs_segments = opt_costs_segments[0]
                revenue = opt_costs_segments[1]
                undefined_options = {
                    tr_proc_costs_shreds: 'transport_shreds',
                    tr_proc_costs_segments: 'transport_segments'}
                tr_proc_costs = min(undefined_options, key=lambda t: t[1])
                transport_mode = undefined_options[tr_proc_costs]
            # in the tuple (x, y, z): x = agent id, y = transport + process net
            # costs
            eol_unique_ids_selected[key] = tr_proc_costs[0]
            if key == 'lifetime_extension':
                costs_eol_pathways[key] = tr_proc_costs[1]
            else:
                costs_eol_pathways[key] = tr_proc_costs[1] + \
                                          decommissioning_cost
            rev_eol_pathways[key] = revenue
            eol_path_transport[key] = transport_mode
        return costs_eol_pathways, rev_eol_pathways, eol_path_transport

    @staticmethod
    def convert_unit_land_cost(waste_volume_model, key, process_costs,
                               transport_mode):
        if waste_volume_model['waste_volume'] and key == 'landfill':
            process_costs_key = process_costs[key]
            # costs without conversion: (1 ton) * $/ton
            # costs with conversion: (1 ton) / ton/m3 * $/ton * ton/m3
            # (first conversion = waste, second conversion = landfill prices)
            conversion_factor = waste_volume_model['land_cost_conv'] / \
                waste_volume_model[transport_mode]
            process_costs_key = tuple([
                (x, y, z * conversion_factor, v * conversion_factor,
                 w * conversion_factor) for x, y, z, v, w in
                process_costs_key])
        else:
            process_costs_key = process_costs[key]
        return process_costs_key

    # TODO: write unittest
    @staticmethod
    def minimum_tr_proc_costs(process_costs, transport_cost):
        """
        Minimize transportation and process costs when several options (eol
        facilities) ara available in a given eol pathway
        :param process_costs: list of tuple containing unique_id, location, and
        process cost of all facilities providing the given eol service
        :param transport_cost: list of tuple containing unique_id and
        transportation costs of all facilities providing the given eol service
        :return: a tuple containing the unique_id of the facility with the
        lowest sum of transportation and process cost (second element of the
        tuple)
        """
        list_process_cost = [(x, z) for x, y, z, v, w in process_costs]
        list_all_cost = transport_cost + list_process_cost
        dic_cost = {x: 0 for x, y in list_process_cost}
        for x, y in list_all_cost:
            if x in dic_cost:
                dic_cost[x] += y
        list_tot_cost = list(map(tuple, dic_cost.items()))
        if list_process_cost:
            minimum_tr_proc_cost = min(list_tot_cost, key=lambda t: t[1])
        else:
            minimum_tr_proc_cost = (np.nan, np.nan)
        revenue_list = [item for item in process_costs if
                        item[0] == minimum_tr_proc_cost[0]]
        if revenue_list:
            revenue = revenue_list[0][4]
        elif process_costs:
            revenue = process_costs[0][4]
        else:
            revenue = 0
        return minimum_tr_proc_cost, revenue

    # TODO: write unittest
    @staticmethod
    def eol_transportation_costs(
            eol_pathways, distances, transport_shred_costs, transport_shreds,
            transport_segment_costs, transport_segments,
            variables_developers_wpo, symetric_triang_distrib_draw,
            mass_conv_factor, t_cap, t_rd, blades_per_rotor):
        """
        Compute transportation costs according for all options: shredded
        blades, cut blades or for repair
        :param eol_pathways: different choices of eol pathways
        :param distances: distances to each eol facility from the Wind farm
        :param transport_shred_costs: function for computing shred costs
        :param transport_shreds: cost model for transporting shredded blades
        :param transport_segment_costs: function for computing segment costs
        :param transport_segments: cost model for transporting segmented blades
        :param variables_developers_wpo: variables from developers used by wpo
        :param symetric_triang_distrib_draw: symetric triangular distribution
        probability density function (single draw)
        :param mass_conv_factor: conversion factor to convert blade waste
        expressed in MW to blade waste expressed in tons
        :param t_cap: turbine capacity (used when blade are transported as
        segments)
        :param t_rd: rotor diameter (used when blade are transported as
        segments)
        :param blades_per_rotor: number of blades per rotor (used when blade
        are transported as segments)
        :return: transportation costs for all options
        """
        eol_tr_costs_shreds = {}
        eol_tr_costs_segments = {}
        eol_tr_costs_repair = {}
        for key in eol_pathways.keys():
            if key in distances:
                eol_tr_costs_shreds[key] = transport_shred_costs(
                    transport_shreds, distances[key],
                    symetric_triang_distrib_draw)
                eol_tr_costs_segments[key] = transport_segment_costs(
                    transport_segments, distances[key], mass_conv_factor,
                    t_cap, t_rd, blades_per_rotor)
            else:
                eol_tr_costs_repair[key] = [
                    (x, y) for x, y, z, v, w in variables_developers_wpo[key]]
        return eol_tr_costs_shreds, eol_tr_costs_segments, eol_tr_costs_repair

    # TODO: write unittest
    @staticmethod
    def transport_shred_costs(data, distances, symetric_triang_distrib_draw):
        """
        Compute costs when blades are shredded before transportation
        :param data: shredding process and transportation costs
        :param distances: distances from wind farm site (where shredding
        occurs) to the eol facility
        :param symetric_triang_distrib_draw: symetric triangular distribution
        probability density function (single draw)
        :return: the cost associated with shredding and transporting shreds
        to the eol site
        """
        shredding_costs = data['shredding_costs']
        shredding_costs = symetric_triang_distrib_draw(
                shredding_costs[0], shredding_costs[1])
        transport_cost_shreds = data['transport_cost_shreds']
        transport_cost_shreds = symetric_triang_distrib_draw(
                    transport_cost_shreds[0], transport_cost_shreds[1])
        # in the tuple: x is agent id, y is the distance to agent, z is
        # agent process net cost, v is agent cost, and w is agent revenue
        cost_shreds = [(x, shredding_costs + transport_cost_shreds * y) for
                       x, y, z, v, w in distances]
        return cost_shreds

    # TODO: write unittest
    @staticmethod
    def transport_segment_costs(data, distances, mass_conv_factor, t_cap,
                                t_rd, blades_per_rotor):
        """
        Compute costs when blades are cut before transportation
        :param data: cutting process and transportation costs
        :param distances: distances from wind farm site (where cutting
        occurs) to the eol facility
        :param mass_conv_factor: conversion factor to convert blade waste
        expressed in MW to blade waste expressed in tons
        :param t_cap: turbine capacity (used when blade are transported as
        segments)
        :param t_rd: rotor diameter (used when blade are transported as
        segments)
        :param blades_per_rotor: number of blades per rotor (used when blade
        are transported as segments)
        :return: the cost associated with cutting and transporting segments
        to the eol site
        """
        cutting_costs = data['cutting_costs']
        transport_cost_segments = data['transport_cost_segments']
        # converting $/truck_load-km in $/m_blade-km
        transport_cost_meter = transport_cost_segments / (
                data['length_segment'] * data['segment_per_truck'])
        mass_to_meter = mass_conv_factor * t_cap / ((
                t_rd / 2) * blades_per_rotor)
        transport_cost_segments = transport_cost_meter / mass_to_meter
        # in the tuple: x is agent id, y is the distance to agent and z is
        # agent process net cost
        cost_segments = [(x, cutting_costs + transport_cost_segments * y)
                         for x, y, z, v, w in distances]
        return cost_segments

    # TODO: write unittest
    @staticmethod
    def eol_distances(possible_destinations_rec, possible_destinations_land,
                      all_possible_distances, t_state, eol_pathways_barriers):
        """
        Compute the distances to all eol facilities for each eol pathway
        :param possible_destinations_rec: all possible destinations for the
        recycling eol pathways
        :param possible_destinations_land: all possible destinations for the
        landfill eol pathway
        :param all_possible_distances: distances to all possible destinations
        :param t_state: state where the project is located
        :param eol_pathways_barriers: report the minimum distance origin-target
        for each eol pathway
        :return: the distances to all eol facilities for each eol pathway
        """
        distances = {}
        possible_destinations = possible_destinations_rec
        origin = t_state
        all_dist = all_possible_distances.loc[origin]
        for key in possible_destinations_land.keys():
            possible_destinations[key] = possible_destinations_land[key]
        for key in possible_destinations.keys():
            list_destinations = possible_destinations[key]
            # in the tuple: x is agent id, y is agent state, z is agent
            # process net cost, v is agent cost, and w is agent revenue
            list_distances = [
                (x, all_dist[y], z, v, w)
                for x, y, z, v, w in list_destinations]
            distances[key] = list_distances
            if list_distances:
                min_distance = min(list_distances, key=lambda t: t[1])[1]
                eol_pathways_barriers[key] = min_distance
            else:
                eol_pathways_barriers[key] = np.nan
        return distances

    @staticmethod
    def atb_model(atb_land_wind, time_step, simulation_start):
        start = atb_land_wind['start']
        end = atb_land_wind['end']
        t_cap_lin_reg_coeff = (end['t_cap'] - start['t_cap']) / \
                              (end['year'] - start['year'])
        t_rd_lin_reg_coeff = (end['t_rd'] - start['t_rd']) / \
                             (end['year'] - start['year'])
        t_cap = start['t_cap'] + t_cap_lin_reg_coeff * \
            (time_step + simulation_start - start['year'])
        t_rd = start['t_rd'] + t_rd_lin_reg_coeff * \
            (time_step + simulation_start - start['year'])
        return t_cap, t_rd

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

    @staticmethod
    def instant_to_cumulative_dic(instant_dic, cumulative_dic):
        """
        Transform a dictionary containing instant value (value of the current
        time-step) into cumulative value (value for the duration of the
        simulation)
        :param instant_dic: the dictionary containing instant values
        :param cumulative_dic: the dictionary containing cumulative values
        :return: the updated dictionary containing cumulative values
        """
        for key, value in instant_dic.items():
            cumulative_dic[key] += value
        return cumulative_dic

    @staticmethod
    def weighted_average(list_weight_elements, list_variables):
        """
        Compute the weighted average from a list of weights (that will be
        normalized) and a list of variables from which the weighted average
        must be found
        :param list_weight_elements: the list of weights
        :param list_variables: the list of variables
        :return: the weighted average
        """
        total_weight = sum(list_weight_elements)
        weights = [x / total_weight for x in list_weight_elements]
        weighted_variables = [x * y for x, y in zip(weights, list_variables)]
        weighted_average = sum(weighted_variables)
        return weighted_average

    @staticmethod
    def divide_value_by_tot_dic(dic):
        # absolute value of total to keep direction of factor (e.g., in the
        # case of the pressure factor)
        tot = abs(np.nansum(list(dic.values())))
        if tot != 0:
            dic = {k: v / tot for k, v in dic.items()}
        return dic

    @staticmethod
    def compute_yearly_or_cum_adoption_ratios(
            yearly_cum_ratios, input_variable, simulation_start,
            clock, categories, past_values, safe_div, yearly):
        categories_new_dict = dict.fromkeys(categories.keys(), 0)
        yearly_cum_value = {}
        total = 0
        for value in input_variable.values():
            for key, value2 in value.items():
                categories_new_dict[key] += value2
        for key in categories_new_dict.keys():
            yearly_cum_value[key] = categories_new_dict[key] - \
                                    past_values[key]
            total += yearly_cum_value[key]
        for key in categories_new_dict.keys():
            yearly_cum_ratios[simulation_start + clock][key] = safe_div(
                yearly_cum_value[key], total)
        if yearly:
            past_values = copy.deepcopy(categories_new_dict)
        else:
            past_values = dict.fromkeys(categories.keys(), 0)
        return yearly_cum_ratios, past_values

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
        self.rec_land_volume = self.initial_dic_from_key_list(
            self.waste_rec_land.keys(), 0)

    def reinitialize_global_variables_rec_land_reg_dev(self):
        """
        Re-initialize yearly variables
        """
        self.variables_recyclers = self.initial_dic_from_key_list(
            self.recyclers.keys(), [])
        self.variables_recyclers_tr = self.initial_dic_from_key_list(
            self.recyclers.keys(), [])
        self.regulations_enacted = self.nested_init_dic(
            False, self.choices_circularity.keys(), self.growth_rates.keys())
        self.le_characteristics = []
        self.dissolution_available = {}
        self.list_tb_lifetimes = []

    def reinitialize_global_variables_dev_man_rec_wpo(self):
        """
        Re-initialize yearly variables
        """
        self.variables_additional_wpo = []
        self.tp_blade_manufactured = 0
        self.tp_blade_demanded = 0
        self.variables_landfills = self.initial_dic_from_key_list(
            self.wbj_database['landfill_type'].unique().tolist(), [])
        self.variables_landfills_tr = self.initial_dic_from_key_list(
            self.wbj_database['landfill_type'].unique().tolist(), [])

    def update_model_variables_start_of_step(self):
        """
        Update model variables at the start of the step
        """
        # Select only mass_conv_factor and p_cap from the tuples in
        # variables_additional_wpo
        self.weighted_avr_mass_conv_factor = self.weighted_average(
            [i[2] for i in self.variables_additional_wpo],
            [i[4] for i in self.variables_additional_wpo])
        self.average_lifetimes_wpo = []
        self.landfill_remaining_cap = self.initial_dic_from_key_list(
            self.growth_rates.keys(), 0)
        self.yearly_waste_ratios, self.past_eol_waste = \
            self.compute_yearly_or_cum_adoption_ratios(
                self.yearly_waste_ratios, self.states_waste_eol_path,
                self.temporal_scope['simulation_start'], self.clock,
                self.eol_pathways, self.past_eol_waste, self.safe_div, True)
        self.cum_blade_ratios = \
            self.compute_yearly_or_cum_adoption_ratios(
                self.cum_blade_ratios, self.blade_type_capacities,
                self.temporal_scope['simulation_start'], self.clock,
                self.blade_types, dict.fromkeys(self.blade_types.keys(), 0),
                self.safe_div, False)[0]
        self.cum_waste_ratios = self.compute_yearly_or_cum_adoption_ratios(
                self.cum_waste_ratios, self.states_waste_eol_path,
                self.temporal_scope['simulation_start'], self.clock,
                self.eol_pathways, dict.fromkeys(self.eol_pathways.keys(), 0),
                self.safe_div, False)[0]
        self.landfill_count = len(self.schedule_land.agents)
        self.average_eol_costs = self.initial_dic_from_key_list(
            self.eol_pathways.keys(), 0)

    def update_model_variables_end_of_step(self):
        """
        Update model variables at the end of the step
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
        self.update_model_variables_start_of_step()
        self.reinitialize_global_variables_wpo()
        self.schedule_wpo.step()
        self.reinitialize_global_variables_rec_land_reg_dev()
        self.schedule_man.step()
        self.schedule_dev.step()
        self.reinitialize_global_variables_dev_man_rec_wpo()
        self.schedule_rec.step()
        self.schedule_land.step()
        self.schedule_reg.step()
        self.schedule.step()
        self.update_model_variables_end_of_step()
        self.adding_state_w_cap(self.add_state_projections,
                                self.temporal_scope, self.clock, self.grid_wpo,
                                self.schedule_wpo, WindPlantOwner)
        self.adding_agents(self.p_install_growth, self.grid_wpo,
                           self.schedule_wpo, WindPlantOwner)
        self.clock += 1
