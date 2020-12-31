# Notes:
# In the event of negative profit (loss), the wind farm owner would need to
# subsidize (pay) to process the end-of-life material. If this is more
# expensive than solid waste disposal, most wind farm owners will
# (and currently do) choose the least-cost option: solid waste disposal.
# You can use Liu et al. 2019 to include energy net impact results as a first
# approximation for adding environmental information to the model
# Think about using the machine learning metamodel to calibrate the ABM
# Think about reinforcement learning
# try to set up different random scheduler? Or create my own random scheduler
# where agent types go one after another?
# Use RandomActivation, you can have multiple schedulers!!!
# Write unittests -  use: https://realpython.com/python-testing/
# The unittest library is already there! Just need to import in a different
# python module
# Create the file unittest and add function as you go?
# Commit quite often  with comments (after each function is written e.g.)
# and do unittests before each commit! (if doesn't pass unittest mention
# in commit comment) (add unittest file to the git repo)


from mesa import Model
from Wind_ABM_Consumer import Consumers
from mesa.time import BaseScheduler
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
                 num_consumers=10):
        self.G = nx.watts_strogatz_graph(num_consumers, 2, 0.1)
        self.grid = NetworkGrid(self.G)
        self.schedule = BaseScheduler(self)
        self.schedule2 = RandomActivation(self)
        for node in self.G.nodes():
            a = Consumers(node, self)
            self.schedule.add(a)
            self.schedule2.add(a)
            self.grid.place_agent(a, node)

        ###
        self.all_states = ['Texas', 'California', 'Montana', 'New Mexico',
                      'Arizona', 'Nevada', 'Colorado', 'Oregon', 'Wyoming',
                      'Michigan', 'Minnesota', 'Utah', 'Idaho', 'Kansas',
                      'Nebraska', 'South Dakota', 'Washington',
                      'North Dakota', 'Oklahoma', 'Missouri', 'Florida',
                      'Wisconsin', 'Georgia', 'Illinois', 'Iowa',
                      'New York', 'North Carolina', 'Arkansas', 'Alabama',
                      'Louisiana', 'Mississippi', 'Pennsylvania', 'Ohio',
                      'Virginia', 'Tennessee', 'Kentucky', 'Indiana',
                      'Maine', 'South Carolina', 'West Virginia',
                      'Maryland', 'Massachusetts', 'Vermont',
                      'New Hampshire', 'New Jersey', 'Connecticut',
                      'Delaware', 'Rhode Island']
        self.states = pd.read_csv("StatesAdjacencyMatrix.csv").to_numpy()
        # Compute distances
        self.mean_distance_within_state = np.nanmean(
            np.where(self.states != 0, self.states, np.nan)) / 2
        self.states_graph = nx.from_numpy_matrix(self.states)
        nodes_states_dic = \
            dict(zip(list(self.states_graph.nodes),
                     list(pd.read_csv("StatesAdjacencyMatrix.csv"))))
        self.states_graph = nx.relabel_nodes(self.states_graph,
                                             nodes_states_dic)
        for i in self.all_states:
            self.recycling_states = [i]
            distances_to_recyclers = []
            distances_to_recyclers = self.shortest_paths(
                self.states_graph, self.recycling_states,
                distances_to_recyclers)

    def shortest_paths(self, graph, target_states, distances_to_target):
        """
        Compute shortest paths between chosen origin states and targets with
        the Dijkstra algorithm.
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
                shortest_paths_closest_target = self.mean_distance_within_state
            distances_to_target.append(shortest_paths_closest_target)
        return distances_to_target

    def step(self):
        """
        Advance the model by one step and collect data.
        """
        self.schedule.step()
        self.schedule2.step()


WindABM().step()



