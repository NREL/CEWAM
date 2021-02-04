# -*- coding:utf-8 -*-
"""
Created on December 31 2020

@author Julien Walzberg - Julien.Walzberg@nrel.gov

Test functions in Wind_ABM_Model
"""


from unittest import TestCase
from Wind_ABM_Model import WindABM
from mesa.time import RandomActivation
from mesa.space import NetworkGrid
from mesa import Agent
import pandas as pd
from collections import Counter

# TODO: complete unittests with TPB and other functions


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
        number_node = WindABM().uswtdb.shape[0]
        theo_avg_node_degree = WindABM().small_world_network["node_degree"]
        rewiring_prob = WindABM().small_world_network["rewiring_prob"]
        graph = WindABM().creating_social_network(
            number_node, theo_avg_node_degree, rewiring_prob)
        graph_node_degrees = graph.degree()
        graph_avg_node_degree = sum(dict(graph_node_degrees).values()) / \
            number_node
        if theo_avg_node_degree % 2 != 0:
            graph_avg_node_degree = graph_avg_node_degree + 1
        self.assertEqual(theo_avg_node_degree, graph_avg_node_degree)

    def test_compute_max_network_size(self):
        """Test that the maximum size of the network is calculated correctly"""
        mock_up_database = pd.DataFrame(
            list(zip([1, 2, 3, 4], ['CO', 'CO', 'CO', 'CO'])),
            columns=['p_year', 't_state'])
        initial_nodes = mock_up_database.shape[0]
        simulation_start = 0
        simulation_end = 3
        coefficient = 2
        result = (simulation_end - simulation_start) * \
            coefficient + initial_nodes
        test_result = WindABM().compute_max_network_size(
            mock_up_database, simulation_start, simulation_end, coefficient)
        self.assertEqual(result, test_result)

    def test_creating_agent(self):
        """Test that agents are created with all attributes"""
        test_param = {"unit": 1, "unit2": 2}
        number_node = WindABM().uswtdb.shape[0]
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

        WindABM().creating_agents(number_node, graph, grid, schedule,
                                  TestAgent, **test_param)
        sum_test = 0
        for a in schedule.agents:
            sum_test += a.test_var["unit"] + a.test_var["unit2"]
        result = number_node * (test_param["unit"] + test_param["unit2"])
        self.assertEqual(sum_test, result)

    def test_adding_agents(self):
        """Test that agents are added to the model"""
        test_param = {"unit": 1, "unit2": 0}
        max_num_agents = 15
        num_agents = 5
        test_model = WindABM()
        test_model.additional_id = max_num_agents - num_agents
        theo_avg_node_degree = 2
        rewiring_prob = 0
        graph = test_model.creating_social_network(
            max_num_agents, theo_avg_node_degree, rewiring_prob)
        schedule = RandomActivation(self)
        grid = NetworkGrid(graph)

        class TestAgent(Agent):
            def __init__(self, unique_id, model, **kwargs):
                super().__init__(unique_id, model)
                """
                Creation of new agent
                """
                self.test_var = kwargs

        test_model.adding_agents(num_agents, grid, schedule, TestAgent,
                                 **test_param)
        sum_test = 0
        for a in schedule.agents:
            sum_test += a.test_var["unit"] + a.test_var["unit2"]
        result = num_agents * (test_param["unit"] + test_param["unit2"])
        self.assertEqual(sum_test, result)

    def test_wind_plant_owner_data(self):
        """Test that the sum of projects' cumulative capacity corresponds to
        projects > 1999, with a cumulative capacity different from 0 and
        limited to the contiguous US"""
        uswtdb_test = WindABM().wind_plant_owner_data(
            WindABM().external_files['uswtdb'], WindABM().state_abrev,
            WindABM().cap_to_diameter_model,
            WindABM().temporal_scope['simulation_start'],
            WindABM().temporal_scope['pre_simulation'])
        result = 110316  # sum of p_cap
        sum_test = round(uswtdb_test['p_cap'].sum())
        self.assertEqual(sum_test, result)

    def test_p_install_growth_model(self):
        """Test that the agent linear growth is computed accordingly"""
        mock_up_database = pd.DataFrame(
            list(zip([1, 2, 3, 4], ['CO', 'CO', 'CO', 'CO'])),
            columns=['p_year', 't_state'])
        result = 1
        test_result = WindABM().p_install_growth_model(mock_up_database)
        self.assertEqual(test_result, result)

    def test_cumulative_capacity_growth(self):
        """Verify that growth model behave as expected"""
        states_cap = {"Colorado": 100.0, "Washington": 50.0}
        additional_cap = states_cap.copy()
        growth_rates = {"Colorado": 0.1, "Washington": 0.2}
        result = list(states_cap.values())
        gr = list(growth_rates.values())
        result = [x * y for x, y in zip(result, gr)]
        additional_cap = WindABM().cumulative_capacity_growth(
            states_cap, growth_rates, additional_cap)
        additional_cap = list(additional_cap.values())
        self.assertCountEqual(result, additional_cap)

    def test_additional_agent_state(self):
        """
        Test that the right numbers of new project state locations are defined
        """
        additional_cap = {"Colorado": 0, "Washington": 9, "Oregon": 1}
        p_install_growth = 10
        result = ["Washington", "Washington", "Washington", "Washington",
                  "Washington", "Washington", "Oregon", "Washington",
                  "Colorado", "Oregon"]
        result = Counter(result)['Washington']
        test_result = WindABM().additional_agent_state(additional_cap,
                                                       p_install_growth)
        test_result = Counter(test_result)['Washington']
        self.assertAlmostEqual(test_result, result, delta=2)

    def test_dic_with_list_item_frequency(self):
        """Test that the function create the appropriate dictionary"""
        test_list = ['Washington', 'Colorado', 'Oregon', 'Colorado',
                     'Washington', 'Washington']
        result = {"Oregon": 1, "Colorado": 2, "Washington": 3}
        test_result = WindABM().dic_with_list_item_frequency(test_list)
        self.assertDictEqual(result, test_result)

    def test_waste_generation(self):
        """Test that waste generation behave as expected"""
        p_cap_waste = 10
        installation_year = 2000
        start_year = 2000
        clock = 2
        avg_lifetime = 3
        weibull_shape_factor = 3
        test_result = round(WindABM().waste_generation(
            start_year, clock, installation_year, p_cap_waste, avg_lifetime,
            weibull_shape_factor), 2)
        result = 2.56
        self.assertEqual(result, test_result)

    def test_initial_dic_from_key_list(self):
        """Test that the function create the appropriate dictionary"""
        test_list = ["Colorado", "Washington", "California"]
        result = {"Colorado": 0, "Washington": 0, "California": 0}
        test_result = WindABM().initial_dic_from_key_list(test_list, 0)
        self.assertDictEqual(result, test_result)

    def test_roulette_wheel(self):
        # TODO
        pass

    def test_dic_cumulative_frequencies(self):
        # TODO
        pass

    def test_re_initialize_global_variable(self):
        """Function can't be formally tested here"""
        pass

    def test_update_model_variables(self):
        """Function can't be formally tested here"""
        pass

    def test_step(self):
        """Test that the model run steps without errors"""
        model = WindABM()
        steps = 2
        clock = 0
        for i in range(steps):
            model.step()
            clock = model.clock
        self.assertEqual(steps, clock)
