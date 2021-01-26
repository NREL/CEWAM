# -*- coding:utf-8 -*-
"""
Created on December 31 2020

@author Julien Walzberg - Julien.Walzberg@nrel.gov

Model - Circular Economy Wind Agent-based Model (CEWAM)
This module contains the model class that creates and activates agents. The
module also defines inputs (default values can be changed by user) and collect
outputs.
"""

# Notes:
# A machine learning metamodel could be used to calibrate the ABM quicker
# Reinforcement learning could be used in the future
# Do unittests before each commit (if doesn't pass unittest mention
# in commit comment)
# Avoid calling the scheduler unless there are no other choices

# TODO: Next steps -
#  2) At this point build a test that check that some simulation results
#  stay what they should be (e.g., after 30 time steps are the results what
#  was obtained in other projections for waste and installed capacity?)
#  3) start TPB
#  4) Continue with other agents

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


class WindABM(Model):
    def __init__(self,
                 seed=None,
                 manufacturers=100,
                 developers=100,
                 recyclers=100,
                 landfills=100,
                 regulators=100,
                 small_world_network={"node_degree": 15, "rewiring_prob": 0.1},
                 external_files={
                     "state_distances": "StatesAdjacencyMatrix.csv", "uswtdb":
                     "uswtdb_v3_3_20210114.csv"},
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
                 blades_per_rotor=3):
        """
        Initiate model.
        :param seed: number used to initialize the random generator
        :param manufacturers: number of manufacturers
        :param developers: number of developers
        :param recyclers: number of reyclers
        :param landfills: number of landfills
        :param regulators: number of regulators
        :param small_world_network: characteristics of the small-world network
        (if rewiring prob set to 0: regular lattice, if set to 1: random
        network)
        :param external_files: dictionary mapping files to their variables
        :param growth_rates: states' wind capacity growth rates
        :param average_lifetime: wind turbines' average lifetime (in years)
        :param weibull_shape_factor: parameter controlling curve's shape in 
        the Weibull function
        :param blade_size_to_mass_model: parameters for a power function 
        y=ax**b relating blade radius and blade mass where y is in tons and x 
        is in meters
        :param cap_to_diameter_model: parameters for a power function 
        converting turbine capacity to rotor diameter
        :param temporal_scope: simulation start and end year and past 
        installations considered
        :param blades_per_rotor: number of blades in rotors to compute blades'
        mass
        """
        # Variables from inputs (value defined externally):
        self.seed = seed
        self.manufacturers = manufacturers
        self.developers = developers
        self.recyclers = recyclers
        self.landfills = landfills
        self.regulators = regulators
        self.small_world_network = small_world_network
        self.external_files = external_files
        self.growth_rates = growth_rates
        self.average_lifetime = average_lifetime
        self.weibull_shape_factor = weibull_shape_factor
        self.blade_size_to_mass_model = blade_size_to_mass_model
        self.cap_to_diameter_model = cap_to_diameter_model
        self.temporal_scope = temporal_scope
        self.blades_per_rotor = blades_per_rotor
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
            self.cap_to_diameter_model, self.temporal_scope['pre_simulation'],
            self.temporal_scope['simulation_start'])
        self.p_install_growth = self.p_install_growth_model(self.uswtdb)
        self.avg_p_cap = self.uswtdb['p_cap'].mean()
        self.additional_id = self.uswtdb.shape[0]
        self.states_cap = self.null_dic_from_key_list(growth_rates.keys())
        self.additional_cap = self.null_dic_from_key_list(growth_rates.keys())
        self.list_agent_states = []
        self.dict_agent_states = {}
        self.number_wpo_agent = 0
        # Computing transportation distances:
        self.state_distances = \
            pd.read_csv(self.external_files["state_distances"])
        self.state_dis_matrix = self.state_distances.to_numpy()
        self.states = self.state_distances.columns.to_list()
        self.states_graph = nx.from_numpy_matrix(self.state_dis_matrix)
        nodes_states_dic = \
            dict(zip(list(self.states_graph.nodes),
                     list(pd.read_csv("StatesAdjacencyMatrix.csv"))))
        self.states_graph = nx.relabel_nodes(self.states_graph,
                                             nodes_states_dic)
        self.all_shortest_paths_or_trg = self.compute_all_distances(
            self.states, self.states_graph)
        # Creating agents and social networks:
        self.schedule = BaseScheduler(self)
        self.G_wpo = self.creating_social_network(
            self.compute_max_network_size(
                self.uswtdb, self.temporal_scope['simulation_start'],
                self.temporal_scope['simulation_end'],
                self.p_install_growth),
            self.small_world_network["node_degree"],
            self.small_world_network["rewiring_prob"])
        self.grid_wpo = NetworkGrid(self.G_wpo)
        self.schedule_wpo = RandomActivation(self)
        self.creating_agents(self.uswtdb.shape[0], self.G_wpo, self.grid_wpo,
                             self.schedule_wpo, WindPlantOwner)
        self.G_man = self.creating_social_network(
            self.manufacturers, self.small_world_network["node_degree"],
            self.small_world_network["rewiring_prob"])
        self.grid_man = NetworkGrid(self.G_man)
        self.schedule_man = RandomActivation(self)
        self.creating_agents(self.manufacturers, self.G_man, self.grid_man,
                             self.schedule_man, Manufacturer)
        self.G_dev = self.creating_social_network(
            self.developers, self.small_world_network["node_degree"],
            self.small_world_network["rewiring_prob"])
        self.grid_dev = NetworkGrid(self.G_dev)
        self.schedule_dev = RandomActivation(self)
        self.creating_agents(self.developers, self.G_dev, self.grid_dev,
                             self.schedule_dev, Developer)
        self.G_rec = self.creating_social_network(
            self.recyclers, self.small_world_network["node_degree"],
            self.small_world_network["rewiring_prob"])
        self.grid_rec = NetworkGrid(self.G_rec)
        self.schedule_rec = RandomActivation(self)
        self.creating_agents(self.recyclers, self.G_rec, self.grid_rec,
                             self.schedule_rec, Recycler)
        self.G_land = self.creating_social_network(
            self.landfills, self.small_world_network["node_degree"],
            self.small_world_network["rewiring_prob"])
        self.grid_land = NetworkGrid(self.G_land)
        self.schedule_land = RandomActivation(self)
        self.creating_agents(self.landfills, self.G_land, self.grid_land,
                             self.schedule_land, Landfill)
        self.G_reg = self.creating_social_network(
            self.regulators, self.small_world_network["node_degree"],
            self.small_world_network["rewiring_prob"])
        self.grid_reg = NetworkGrid(self.G_reg)
        self.schedule_reg = RandomActivation(self)
        self.creating_agents(self.regulators, self.G_reg, self.grid_reg,
                             self.schedule_reg, Regulator)
        # Create data collectors:
        model_reporters = {
            "Year": lambda a:
            self.clock + self.temporal_scope['simulation_start'],
            "Cumulative capacity (MW)": lambda a: self.all_cap,
            "Cumulative waste (MW)": lambda a: self.all_waste,
            "Number wpo agents": lambda a: self.number_wpo_agent}
        agent_reporters = {
            "State": lambda a: getattr(a, "t_state", None),
            "Capacity (MW)": lambda a: getattr(a, "p_cap", None),
            "Cumulative waste (MW)": lambda a: getattr(a, "cum_waste", None),
            "Mass conversion factor": lambda a:
            getattr(a, "mass_conv_factor", None)}
        self.data_collector = DataCollector(
            model_reporters=model_reporters,
            agent_reporters=agent_reporters)

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
    def creating_social_network(nodes, node_degree,
                                rewiring_prob):
        """
        Set up model's social networks with the Watts & Strogatz algorithm.
        :param nodes: number of nodes in the graph
        :param node_degree: node degree of the equivalent regular lattice
        :param rewiring_prob: probability of rewiring a given edge
        :return social_network: a graph representing agents' social network
        """
        social_network = nx.watts_strogatz_graph(nodes, node_degree,
                                                 rewiring_prob)
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
            grid.place_agent(a, self.additional_id)
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
        uswtdb = uswtdb[(uswtdb['p_year'] >= start_year) &
                        (uswtdb['p_year'] <= pre_simulation)]
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
        Grow the list of yearly installed capacity according to growth rate
        and update the cumulative installed capacity
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

    @staticmethod
    def additional_agent_state(additional_cap, p_install_growth):
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
            list_cumprob = np.cumsum(list(state_add_cap_prop.values()))
            state_add_cap_cumprob = dict(zip(state_add_cap_prop.keys(),
                                             list_cumprob))
            max_prob = max(state_add_cap_cumprob.values())
            for i in range(p_install_growth -
                           len(list_agent_states)):
                pick = random.uniform(0, max_prob)
                current = 0
                for key, value in state_add_cap_cumprob.items():
                    current += value
                    if value > pick:
                        list_agent_states.append(key)
                        break
        random.shuffle(list_agent_states)
        return list_agent_states

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
    def null_dic_from_key_list(key_list):
        """
        Create an empty dictionary with keys taken from a list
        :param key_list: the list of keys
        :return: the empty dictionary with corresponding keys
        """
        null_dic = {}
        for i in key_list:
            null_dic[i] = 0
        return null_dic

    def re_initialize_global_variable(self):
        """
        Re-initialize yearly variables
        """
        self.number_wpo_agent = 0

    def update_model_variables(self):
        """
        Update model variables
        """
        self.additional_cap = self.cumulative_capacity_growth(
            self.states_cap, self.growth_rates, self.additional_cap)
        self.list_agent_states = \
            self.additional_agent_state(self.additional_cap,
                                        self.p_install_growth)
        self.dict_agent_states = self.dic_with_list_item_frequency(
            self.list_agent_states)

    def step(self):
        """
        Advance the model by one step and collect data.
        """
        self.data_collector.collect(self)
        self.re_initialize_global_variable()
        self.schedule_wpo.step()
        self.schedule_man.step()
        self.schedule_dev.step()
        self.schedule_rec.step()
        self.schedule_land.step()
        self.schedule_reg.step()
        self.schedule.step()
        self.update_model_variables()
        self.adding_agents(self.p_install_growth, self.grid_wpo,
                           self.schedule_wpo, WindPlantOwner)
        self.clock += 1
