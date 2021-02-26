# -*- coding:utf-8 -*-
"""
Created on December 31 2020

@author Julien Walzberg - Julien.Walzberg@nrel.gov

Test functions in Wind_ABM_WindPlantOwner
"""

from unittest import TestCase
from Wind_ABM_Model import WindABM
import random


class TestWindPlantOwner(TestCase):
    def setUp(self):
        self.t_model_inst = WindABM(eol_pathways={
            "lifetime_extension": True, "dissolution": True,
            "pyrolysis": True, "mechanical_recycling": True,
            "cement_co_processing": True, "landfill": True})

    def test_wind_power_capacity_state_distribution(self):
        """Verify that capacities are distributed as should be within the US"""
        schedule = self.t_model_inst.schedule_wpo
        test_uswtdb = self.t_model_inst.uswtdb.drop(['p_name'], axis=1)
        test_uswtdb = test_uswtdb.groupby(['t_state']).sum()
        value = []
        test_score = []
        for index, row in test_uswtdb.iterrows():
            test_sum = 0
            for a in schedule.agents:
                if a.t_state == index:
                    test_sum += a.p_cap
            if test_sum == row['p_cap']:
                test_score.append(True)
            else:
                test_score.append(False)
            value.append(True)
        self.assertCountEqual(value, test_score)

    def test_compute_mass_conv_factor(self):
        """Verify that conversion factor is computed correctly"""
        rotor_diameter = 20
        coefficient = 0.5
        power = 2
        blades_per_rotor = 3
        t_cap = 10
        result = coefficient * (rotor_diameter / 2)**power * \
            blades_per_rotor / t_cap
        test_model = self.t_model_inst
        agent = random.choice(test_model.schedule_wpo.agents)
        test_result = agent.compute_mass_conv_factor(
            rotor_diameter, coefficient, power, blades_per_rotor, t_cap)
        self.assertEqual(result, test_result)

    def test_conversion_blade_to_ton(self):
        """Test that conversion works properly"""
        mass_conv_factor = 10
        t_cap = 6
        blades_per_rotor = 3
        result = mass_conv_factor * t_cap / blades_per_rotor
        agent = random.choice(self.t_model_inst.schedule_wpo.agents)
        test = agent.conversion_blade_to_ton(mass_conv_factor, t_cap,
                                             blades_per_rotor)
        self.assertEqual(result, test)

    def test_convert_developer_costs(self):
        """Test that costs are converted for all value in dic"""
        developer_costs = {'a': [(1, 2, 6)], 'b': [(3, 4, 12),
                                                   (7, 8, 2)]}
        conversion_factor = 2
        result = {'a': [(1, 2, 3)], 'b': [(3, 4, 6), (7, 8, 1)]}
        agent = random.choice(self.t_model_inst.schedule_wpo.agents)
        test = agent.convert_developer_costs(
            developer_costs, conversion_factor)
        self.assertEqual(result, test)

    def test_eol_distances(self):
        """Test that eol distances are computed correctly"""
        possible_destination_rec = {
            'a': [(1, 'Colorado', 2), (1, 'California', 2)],
            'b': [(1, 'Colorado', 2), (1, 'Washington', 2)]}
        possible_destination_land = {
            'c': [(1, 'Colorado', 2), (1, 'California', 2)]}
        all_possible_distances = self.t_model_inst.all_shortest_paths_or_trg
        agent = random.choice(self.t_model_inst.schedule_wpo.agents)
        agent.t_state = 'Washington'
        result = {
            'a': [(1, 1409, 2), (1, 1045, 2)],
            'b': [(1, 1409, 2), (1, 198, 2)],
            'c': [(1, 1409, 2), (1, 1045, 2)]}
        test = agent.eol_distances(
            possible_destination_rec, possible_destination_land,
            all_possible_distances)
        for key, value in test.items():
            list_distances = test[key]
            list_distances = [(x, round(y), z) for x, y, z in list_distances]
            test[key] = list_distances
        self.assertEqual(test, result)

    def test_transport_shred_costs(self):
        """Test that costs are computed correctly"""
        data = {'transport_cost_shreds': [1, 1.0001],
                'shredding_costs': [2, 2.0001]}
        distances = [(1, 1409, 2), (1, 1045, 2)]
        result = [(1, 2 + 1 * 1409), (1, 2 + 1 * 1045)]
        agent = random.choice(self.t_model_inst.schedule_wpo.agents)
        test = agent.transport_shred_costs(data, distances)
        test = [(x, round(y)) for x, y in test]
        self.assertEqual(result, test)

    def test_transport_segment_costs(self):
        """Test that costs are computed correctly"""
        data = {'transport_cost_segments': 1,
                'cutting_costs': 1, 'length_segment': 1,
                'segment_per_truck': 1}
        distances = [(1, 1409, 2), (1, 1045, 2)]
        result = [(1, 1 + 1 * 1409), (1, 1 + 1 * 1045)]
        agent = random.choice(self.t_model_inst.schedule_wpo.agents)
        agent.mass_conv_factor = 1
        agent.t_cap = 1
        agent.t_rd = 2
        agent.model.blades_per_rotor = 1
        test = agent.transport_segment_costs(data, distances)
        test = [(x, round(y)) for x, y in test]
        self.assertEqual(result, test)

    def test_eol_transportation_costs(self):
        """Test transportation costs"""
        distances = {
            'a': [(1, 1409, 2), (1, 1045, 2)],
            'b': [(1, 1409, 2), (1, 198, 2)]}
        agent = random.choice(self.t_model_inst.schedule_wpo.agents)
        agent.model.eol_pathways = {'a': True, 'b': True, 'c': True}
        agent.model.transport_shreds = {
            'transport_cost_shreds': [1, 1.0001],
            'shredding_costs': [1, 1.0001]}
        agent.model.transport_segments = {
            'transport_cost_segments': 1, 'cutting_costs': 1,
            'length_segment': 1, 'segment_per_truck': 1}
        agent.mass_conv_factor = 1
        agent.t_cap = 1
        agent.t_rd = 2
        agent.model.blades_per_rotor = 1
        agent.variables_developers_wpo = {'c': [(1, 1, 1)]}
        result = (
            {'a': [(1, 1410), (1, 1046)],
             'b': [(1, 1410), (1, 199)]},
            {'a': [(1, 1410), (1, 1046)],
             'b': [(1, 1410), (1, 199)]},
            {'c': [(1, 1)]})
        test1, test2, test3 = agent.eol_transportation_costs(distances)
        test = [test1, test2, test3]
        for i in range(len(test)):
            sub_test = test[i]
            for key, value in sub_test.items():
                list_costs = sub_test[key]
                list_costs = [(x, round(y)) for x, y in list_costs]
                sub_test[key] = list_costs
            test[i] = sub_test
        test = (test[0], test[1], test[2])
        self.assertEqual(test, result)

    def test_costs_eol_pathways(self):
        """Test that costs are minimized"""
        eol_tr_costs_shreds = {'a': [(1, 1), (2, 1)],
                               'b': [(1, 1), (2, 1)],
                               'c': [(1, 2), (2, 4)]}
        eol_tr_costs_segment = {'a': [(1, 1), (2, 1)],
                                'b': [(1, 1), (2, 1)],
                                'c': [(1, 3), (2, 4)]}
        eol_tr_costs_repair = {'d': [(1, 1)]}
        variables_recyclers = {
            'a': [(1, 'Colorado', 1), (2, 'California', 2)],
            'b': [(1, 'Colorado', 2), (2, 'Washington', 1)]}
        variables_landfills = {
            'c': [(1, 'Colorado', 2), (2, 'California', 1)]}
        variables_developers = {'d': [(1, 1, 1)]}
        decommissioning_cost = 0
        agent = random.choice(self.t_model_inst.schedule_wpo.agents)
        agent.model.eol_pathways = {'a': True, 'b': True, 'c': True, 'd': True}
        agent.model.eol_pathways_transport_mode = {
            'a': 'undefined', 'b': 'undefined', 'c': 'undefined',
            'd': 'transport_repair'}
        result = {'a': 2, 'b': 2, 'c': 4, 'd': 2}
        test = agent.costs_eol_pathways(
            eol_tr_costs_shreds, eol_tr_costs_segment, eol_tr_costs_repair,
            variables_recyclers, variables_landfills, variables_developers,
            decommissioning_cost)
        self.assertEqual(result, test)

    def test_minimum_tr_proc_costs(self):
        """Test that costs are minimized"""
        process_costs = [(1, 'Colorado', 4), (2, 'California', 3),
                         (3, 'Indiana', 2), (4, 'Washington', 1)]
        transport_cost = [(1, 2), (2, 5), (3, 5), (4, 7)]
        result = (1, 4 + 2)
        agent = random.choice(self.t_model_inst.schedule_wpo.agents)
        test = agent.minimum_tr_proc_costs(process_costs, transport_cost)
        self.assertEqual(result, test)

    def test_report_variables_if_lifetime_extended_or_else(self):
        """Test that waste is directed correctly"""
        eol_pathway1 = "lifetime_extension"
        eol_second_choice1 = "b"
        state1 = 'Colorado'
        waste1 = 1
        eol_pathway2 = "c"
        eol_second_choice2 = "b"
        state2 = 'Washington'
        waste2 = 2
        reporter_waste = {
            'Colorado': {'lifetime_extension': 0, 'b': 0, 'c': 0},
            'Washington': {'lifetime_extension': 0, 'b': 0, 'c': 0}}
        reporter_adoption = {'lifetime_extension': 0, 'b': 0, 'c': 0}
        mass_conv_factor = 2
        agent = random.choice(self.t_model_inst.schedule_wpo.agents)
        # noinspection PyUnusedLocal
        test1 = agent.report_variables_if_lifetime_extended_or_else(
            eol_pathway1, eol_second_choice1, reporter_waste,
            reporter_adoption, state1, waste1, mass_conv_factor)
        # noinspection PyUnusedLocal
        test2 = agent.report_variables_if_lifetime_extended_or_else(
            eol_pathway2, eol_second_choice2, reporter_waste,
            reporter_adoption, state2, waste2, mass_conv_factor)
        test = [reporter_waste, reporter_adoption]
        results = [{
            'Colorado': {'lifetime_extension': 0, 'b': 2, 'c': 0},
            'Washington': {'lifetime_extension': 0, 'b': 0, 'c': 4}},
            {'lifetime_extension': 1, 'b': 1, 'c': 1}]
        self.assertCountEqual(test, results)

    def test_regulations_consequences(self):
        """Function can't be formally tested here"""
        pass

    def test_update_agent_variables_every_or_specific_step(self):
        """Function can't be formally tested here"""
        pass

    def test_report_agent_variable_once_or_every_step(self):
        """Function can't be formally tested here"""
        pass

    def test_remove_agent(self):
        """Test that agent is removed"""
        test_model = self.t_model_inst
        num_agents = len(test_model.schedule_wpo.agents)
        agent = test_model.schedule_wpo.agents[0]
        agent.p_cap_waste = 0
        agent.remove_agent()
        test_result = len(test_model.schedule_wpo.agents)
        result = num_agents - 1
        self.assertEqual(test_result, result)

    def test_step(self):
        """Test that the wpo agents run steps without errors"""
        model = self.t_model_inst
        agent = random.choice(model.schedule_wpo.agents)
        steps = 1
        agent.step()
        clock = agent.internal_clock
        self.assertEqual(steps, clock)
