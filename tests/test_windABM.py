# -*- coding:utf-8 -*-
"""
Created on December 31 2020

@author Julien Walzberg - Julien.Walzberg@nrel.gov

Model - Circular Economy Wind Agent-based Model (CEWAM)
This module contains the model class that creates and activates agents. The
module also defines inputs (default values can be changed by user) and collect
outputs.
"""


from unittest import TestCase
from Wind_ABM_Model import WindABM
from mesa.time import RandomActivation
from mesa.space import NetworkGrid
from mesa import Agent
from mesa.time import BaseScheduler
import pandas as pd


class TestWindABM(TestCase):
    def test_compute_all_distances(self):
        """Test that distances are computed correctly"""
        states = ["Colorado", "Florida", "Michigan"]
        graph = WindABM().states_graph
        output_distances = WindABM().compute_all_distances(states, graph)
        test_values = round(output_distances.sum(axis=1))
        results = [67591, 81621, 68469]
        self.assertCountEqual(test_values.tolist(), results)

    def test_shortest_paths(self):
        """Test that it find the shortest paths"""
        sum_distances = []
        test_graph = WindABM().states_graph
        targets = ["Washington", "Arkansas", "New York"]
        for i in targets:
            distances = []
            distances = WindABM().shortest_paths(test_graph, [i], distances)
            sum_distances.append(round(sum(distances)))
        results = [104283, 55705, 72433]
        self.assertCountEqual(sum_distances, results)

    def test_creating_social_network_avg_node_degree(self):
        """Test that the network is built with the right average node degree"""
        number_node = WindABM().wind_plant_owner
        theo_avg_node_degree = WindABM().small_world_network["node_degree"]
        rewiring_prob = WindABM().small_world_network["rewiring_prob"]
        graph = WindABM().creating_social_network(
            number_node, theo_avg_node_degree, rewiring_prob)
        graph_node_degrees = graph.degree()
        graph_avg_node_degree = sum(dict(graph_node_degrees).values()) / \
            number_node
        self.assertEqual(theo_avg_node_degree, graph_avg_node_degree)

    def test_creating_agent(self):
        """Test that agents are created with all attributes"""
        test_param = {"unit": 1, "unit2": 2}
        number_node = WindABM().wind_plant_owner
        theo_avg_node_degree = WindABM().small_world_network["node_degree"]
        rewiring_prob = WindABM().small_world_network["rewiring_prob"]
        graph = WindABM().creating_social_network(
            number_node, theo_avg_node_degree, rewiring_prob)
        schedule = RandomActivation(self)
        grid = NetworkGrid(graph)

        class TestAgent(Agent):
            def __init__(self, unique_id, model, **kwargs):
                super().__init__(unique_id, model)
                """
                Creation of new agent
                """
                self.test_var = kwargs

        WindABM().creating_agents(graph, grid, schedule, TestAgent,
                                  **test_param)
        sum_test = 0
        for a in schedule.agents:
            sum_test += a.test_var["unit"] + a.test_var["unit2"]
        result = number_node * (test_param["unit"] + test_param["unit2"])
        self.assertEqual(sum_test, result)

    def test_wind_plant_owner_data(self):
        """Test that the sum of projects' cumulative capacity corresponds to
        projects > 1999, with a cumulative capacity different from 0 and
        limited to the contiguous US"""
        uswtdb_test = WindABM().wind_plant_owner_data(
            WindABM().external_files['uswtdb'], WindABM().state_abrev)
        result = 106229  # sum of p_cap
        sum_test = round(uswtdb_test['p_cap'].sum())
        self.assertEqual(sum_test, result)

    def test_re_initialize_global_variable(self):
        """Function can't be formally tested here"""
        pass

    """
    Method is not used at the moment, consider removing it
    
    def test_aggregate_agent_output(self):
        test_param = 1
        agents = 10
        schedule = BaseScheduler(self)

        class TestAgent(Agent):
            def __init__(self, unique_id, model, param):
                super().__init__(unique_id, model)
                ""
                Creation of new agent
                ""
                self.param = param

        for a in range(agents):
            a = TestAgent(a, WindABM(), test_param)
            schedule.add(a)
        result = test_param * agents
        test_result = WindABM().aggregate_agent_output(schedule, "param")
        self.assertEqual(result, test_result)
    """

    def test_step(self):
        """Test that the model run steps without errors"""
        WindABM().step()
