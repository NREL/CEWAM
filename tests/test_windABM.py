# -*- coding:utf-8 -*-
"""
Created on December 31 2020

@author Julien Walzberg - Julien.Walzberg@nrel.gov

Test functions in Wind_ABM_Model
"""


from unittest import TestCase
from Wind_ABM_Model import WindABM
from Wind_ABM_Recycler import Recycler
from mesa.time import RandomActivation
from mesa.space import NetworkGrid
from mesa import Agent
import pandas as pd
from collections import Counter
import statistics

# TODO: Add a test of the wpo network small-worldness?


class TestWindABM(TestCase):
    def test_network_grid_schedule_agents(self):
        """Test that network has the right number of nodes, that the grid and
        the schedule contains the appropriate number of agents, and that the
        schedule"""
        num_nodes = 100
        node_degree = 5
        rewiring_prob = 0.1
        num_agents = 50
        agent_type = Recycler
        network, grid, schedule = WindABM().network_grid_schedule_agents(
            num_nodes, node_degree, rewiring_prob, num_agents, agent_type)
        results = [100, 50, 50]
        count = 0
        for i in range(num_nodes):
            if grid.is_cell_empty(i):
                count += 1
        agents_in_grid = num_nodes - count
        test_results = [len(network), agents_in_grid, len(schedule.agents)]
        self.assertCountEqual(results, test_results)

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
            number_node, theo_avg_node_degree, rewiring_prob, None)
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
            number_node, theo_avg_node_degree, rewiring_prob, None)
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
        test_model.additional_id = (max_num_agents - num_agents) + \
            test_model.first_wpo_id
        theo_avg_node_degree = 2
        rewiring_prob = 0
        graph = test_model.creating_social_network(
            max_num_agents, theo_avg_node_degree, rewiring_prob, None)
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

    def test_roulette_wheel_choice(self):
        """Test that choice is done according to roulette wheel"""
        dic_frequencies = {'a': 6, 'b': 3, 'c': 3, 'd': 0, 'e': 4}
        num_choices = 16
        deterministic = True
        list_choice = []
        result = ['a'] * 6 + ['b'] * 3 + ['c'] * 3 + ['d'] * 0 + ['e'] * 4
        test = WindABM().roulette_wheel_choice(dic_frequencies, num_choices,
                                               deterministic, list_choice)
        self.assertCountEqual(result, test)

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

    def test_nested_init_dic(self):
        """Test that a 2-level nested dictionary is constructed"""
        initial_value = 'Test'
        dic1 = ['a', 'b']
        dic2 = ['c', 'd', 'e']
        test = WindABM().nested_init_dic(initial_value, dic1, dic2)
        result = {'a': {'c': 'Test', 'd': 'Test', 'e': 'Test'},
                  'b': {'c': 'Test', 'd': 'Test', 'e': 'Test'}}
        self.assertEqual(test, result)

    def test_roulette_wheel(self):
        """Test that the right key is returned when using the roulette wheel"""
        pick = 0.3
        cum_prob_dic = {'test1': 0.1, 'test2': 0.2, 'test3': 0.7, 'test4': 1}
        result = 'test3'
        test = WindABM().roulette_wheel(pick, cum_prob_dic)
        self.assertEqual(result, test)

    def test_dic_cumulative_frequencies(self):
        """Test that a cumulative dictionary is built from frequencies"""
        dic_frequencies = {'a': 200, 'b': 300, 'c': 100, 'd': 53, 'e': 0,
                           'f': 656}
        result = {'a': 200, 'b': 500, 'c': 600, 'd': 653, 'e': 653, 'f': 1309}
        test = WindABM().dic_cumulative_frequencies(dic_frequencies)
        self.assertEqual(result, test)

    def test_remove_item_dic_from_boolean_dic(self):
        """Test that all False value are remove from dic"""
        dic = {'a': 3, 'b': 4, 'c': 5}
        boolean_dic = {'a': False, 'b': False, 'c': False}
        result = {}
        test = WindABM().remove_item_dic_from_boolean_dic(dic, boolean_dic)
        self.assertEqual(result, test)

    def test_attitude(self):
        """Test that attitude scores are correctly computed"""
        ce_att_level = 0.6
        conv_att_level = 0.55
        dic_choices = {'a': None, 'b': None, 'c': None}
        choices_circularity = {'a': True, 'b': False, 'c': True, 'd': False}
        result = {'a': 0.6, 'b': 0.55, 'c': 0.6}
        test = WindABM().attitude(ce_att_level, conv_att_level, dic_choices,
                                  choices_circularity)
        self.assertEqual(result, test)

    def test_subjective_norms(self):
        """Test that subjective norms scores are correctly computed"""
        num_nodes = 10
        node_degree = 2
        rewiring_prob = 0
        num_agents = 10

        class TestAgent(Agent):
            def __init__(self, unique_id, model):
                super().__init__(unique_id, model)
                """
                Creation of new agent
                """
                self.test_var = 'a'

        network, grid, schedule = WindABM().network_grid_schedule_agents(
            num_nodes, node_degree, rewiring_prob, num_agents, TestAgent)
        dic_choices = {'a': True, 'b': True, 'c': True}
        agent = schedule.agents[0]
        position = agent.pos
        result = {'a': 1, 'b': 0, 'c': 0}
        test = WindABM().subjective_norms(grid, 'test_var', position,
                                          dic_choices)
        self.assertEqual(result, test)

    def test_perceived_behavioral_control_and_barriers(self):
        """Test that perceived behavioral control scores are correctly
        computed"""
        value_choices = {'a': -1, 'b': 9, 'c': 10}
        result = {'a': 0, 'b': 0.9, 'c': 1}
        test = WindABM().perceived_behavioral_control_and_barrier(
            value_choices)
        self.assertEqual(result, test)

    def test_pressure(self):
        """Test that pressure scores are correctly computed"""
        state = 'Colorado'
        regulations = {'a': {'Colorado': True, 'California': False,
                             'Washington': False},
                       'b': {'Colorado': False, 'California': False,
                             'Washington': False},
                       'c': {'Colorado': True, 'California': True,
                             'Washington': True}}
        result = {'a': 0.45, 'b': 0, 'c': 1}
        test = WindABM().pressure(state, regulations)
        test = {key: round(value, 2) for key, value in test.items()}
        self.assertEqual(result, test)

    def test_theory_planned_behavior_model(self):
        """Test that scores are added correctly and that the two choices with
        highest scores are returned"""
        tpb_weights = {'w_bi': 0.3, 'w_sn': 1, 'w_a': 1, 'w_pbc': 1,
                       'w_b': 0.3, 'w_p': 0.3}
        ce_att_level = 0.6
        conv_att_level = 0.55
        choices_circularity = {'a': True, 'b': False, 'c': True, 'd': False}
        num_nodes = 10
        node_degree = 2
        rewiring_prob = 0
        num_agents = 10

        class TestAgent(Agent):
            def __init__(self, unique_id, model):
                super().__init__(unique_id, model)
                """
                Creation of new agent
                """
                self.test_var = 'a'

        network, grid, schedule = WindABM().network_grid_schedule_agents(
            num_nodes, node_degree, rewiring_prob, num_agents, TestAgent)
        dic_choices = {'a': True, 'b': True, 'c': True}
        agent = schedule.agents[0]
        position = agent.pos
        cost_choices = {'a': -1, 'b': 9, 'c': 10}
        barrier_choices = {'a': -1, 'b': 9, 'c': 10}
        state = 'Colorado'
        regulations = {'a': {'Colorado': False, 'California': False,
                             'Washington': False},
                       'b': {'Colorado': False, 'California': False,
                             'Washington': False},
                       'c': {'Colorado': True, 'California': True,
                             'Washington': True}}
        att = {'a': 0.6, 'b': 0.55, 'c': 0.6}
        sn = {'a': 1, 'b': 0, 'c': 0}
        pbc = {'a': 0, 'b': 0.9, 'c': 1}
        bar = {'a': 0, 'b': 0.9, 'c': 1}
        press = {'a': 0, 'b': 0, 'c': 1}
        test_dic = {'a': None, 'b': None, 'c': None}
        for key in test_dic.keys():
            test_dic[key] = 0.3 * (1 * att[key] + 1 * sn[key] + 1 * pbc[key]) \
                            + 0.3 * bar[key] + 0.3 * press[key]
        choice1 = max(test_dic, key=test_dic.get)
        test_dic.pop(choice1)
        choice2 = max(test_dic, key=test_dic.get)
        result = (choice1, choice2)
        test1, test2 = WindABM().theory_planned_behavior_model(
            tpb_weights, ce_att_level, conv_att_level, dic_choices,
            choices_circularity, grid, 'test_var', position, cost_choices,
            barrier_choices, state, regulations)
        test = (test1, test2)
        self.assertEqual(result, test)

    def test_lifetime_extension(self):
        """Test that years are added to initial lifetime and share of first
         choice is computed"""
        eol_pathway = 'lifetime_extension'
        initial_lifetime = 10
        le_feas_years = (0.2, 2)
        result = (12, 0.8)
        test1, test2 = WindABM().lifetime_extension(
            eol_pathway, initial_lifetime, le_feas_years)
        test = (test1, test2)
        self.assertEqual(result, test)

    def test_boolean_dic_based_on_dicts(self):
        """Test that Booleans in a dictionary are modified according to other
        Boolean dictionaries"""
        dic_to_modify = {'a': True, 'b': True, 'c': True, 'd': True}
        value_to_change = True
        modifier = False
        dic1 = {'a': True, 'b': False}
        dic2 = {'b': True, 'c': False, 'd': True}
        result = {'a': False, 'b': False, 'c': True, 'd': False}
        test = WindABM().boolean_dic_based_on_dicts(
            dic_to_modify, value_to_change, modifier, dic1, dic2)
        self.assertEqual(result, test)

    def test_filter_list(self):
        """Test that list is filtered out of the desired value"""
        input_list = [1, 2, 'Test', 4, 5]
        filtered_out_value = 'Test'
        result = [1, 2, 4, 5]
        test = WindABM().filter_list(input_list, filtered_out_value)
        self.assertEqual(result, test)

    def test_safe_div(self):
        """Test that division return 0 if denominator is 0"""
        x = 1
        y = 0
        result = 0
        test = WindABM().safe_div(x, y)
        self.assertEqual(result, test)

    def test_trunc_normal_distrib_draw(self):
        """Test that draws are higher than lower bound and lower than higher
        bound and that mean and standard deviation are reasonably close to
        distribution's parameter"""
        a = 0
        b = 1
        loc = 0.5
        scale = 0.1
        values = []
        for i in range(10):
            draw = WindABM().trunc_normal_distrib_draw(a, b, loc, scale)
            values.append(draw)
        mean = sum(values) / len(values)
        std = statistics.stdev(values)
        self.assertGreater(min(values), a)
        self.assertLess(max(values), b)
        self.assertAlmostEqual(mean, loc, delta=0.1)
        self.assertAlmostEqual(std, scale, delta=0.1)

    def test_symetric_triang_distrib_draw(self):
        """Test that draws are higher than lower bound and lower than higher
        bound and that mean is reasonably close distribution's parameter"""
        a = 0
        b = 1
        mean = (b - a) / 2
        values = []
        for i in range(10):
            draw = WindABM().symetric_triang_distrib_draw(a, b)
            values.append(draw)
        test_mean = sum(values) / len(values)
        self.assertGreater(min(values), a)
        self.assertLess(max(values), b)
        self.assertAlmostEqual(mean, test_mean, delta=0.1)

    def test_re_initialize_global_variables_wpo(self):
        """Function can't be formally tested here"""
        pass

    def test_re_initialize_global_other_agents(self):
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
