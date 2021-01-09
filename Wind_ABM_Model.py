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
# Several random scheduler can be defined in one model
# Do unittests before each commit (if doesn't pass unittest mention
# in commit comment)
# Avoid calling the scheduler unless there are no other choices


from mesa import Model
from Wind_ABM_WindPlantOwner import WindPlantOwner
from Wind_ABM_Manufacturer import Manufacturer
from mesa.time import RandomActivation
from mesa.space import NetworkGrid
from mesa.datacollection import DataCollector
import networkx as nx
import numpy as np
from math import *
import matplotlib.pyplot as plt
import pandas as pd
import random
import time


class WindABM(Model):
    def __init__(self,
                 seed=None,
                 wind_plant_owner=10,
                 manufacturers=5,
                 unit=1,
                 unit2=2,
                 small_world_network={"node_degree": 2, "rewiring_prob": 0.1},
                 external_files={
                     "state_distances": "StatesAdjacencyMatrix.csv"}):
        """
        Initiate model.
        :param seed: number used to initialize the random generator
        :param wind_plant_owner: number of wind plant owners
        :param small_world_network: characteristics of the small-world network
        (if rewiring prob set to 0: regular lattice, if set to 1: random
        network)
        :param external_files: dictionary mapping files to their variables
        """
        self.seed = seed
        self.wind_plant_owner = wind_plant_owner
        self.manufacturers = manufacturers
        self.unit = unit
        self.unit2 = unit2
        self.small_world_network = small_world_network
        self.external_files = external_files
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
        self.G = self.creating_social_network(
            self.wind_plant_owner, self.small_world_network["node_degree"],
            self.small_world_network["rewiring_prob"])
        self.grid = NetworkGrid(self.G)
        self.schedule = RandomActivation(self)
        self.creating_agents(self.G, self.grid, self.schedule, WindPlantOwner,
                             unit=self.unit)
        self.G2 = self.creating_social_network(
            self.manufacturers, self.small_world_network["node_degree"],
            self.small_world_network["rewiring_prob"])
        self.grid2 = NetworkGrid(self.G2)
        self.schedule2 = RandomActivation(self)
        self.creating_agents(self.G2, self.grid2, self.schedule2,
                             Manufacturer, unit=self.unit2)
        # TODO:
        #  1) Create other agents Python modules with dummy agent classes
        #  2) Once module are created, write code to create agents and agent
        #  networks

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
    def creating_social_network(nodes, node_degree, rewiring_prob):
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

    def creating_agents(self, social_network, grid, schedule, agent_type,
                        **kwargs):
        """
        Create agents and assign their attributes. Link agents to nodes in the
        social network with the node labels equal to the agent unique id.
        :param social_network: social network linking agents
        :param grid: equivalent graph in Mesa's space
        :param schedule: Mesa scheduler of the agent type
        :param agent_type: name of the agent type, must be similar to the
        agent class's name
        """
        for node in social_network:
            a = agent_type(node, self, **kwargs)
            schedule.add(a)
            grid.place_agent(a, node)

    def step(self):
        """
        Advance the model by one step and collect data.
        """
        self.schedule.step()
        self.schedule2.step()


WindABM().step()



