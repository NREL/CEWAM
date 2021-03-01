# -*- coding:utf-8 -*-
"""
Created on February 25 2021

@author Julien Walzberg - Julien.Walzberg@nrel.gov

Test functions in Wind_ABM_Developer
"""

from unittest import TestCase
from Wind_ABM_Model import WindABM
import random


class TestDeveloper(TestCase):
    def setUp(self):
        self.t_model_inst = WindABM()

    def test_additional_cap(self):
        """Function can't be formally tested here"""
        pass

    def test_assign_wpo_blade_type(self):
        """
        Test that blade type are distributed according to TPB and respect
        supply constraints
        """
        assigned_wpo = [(1, 3, 4, 'Colorado'), (2, 5, 6, 'California')]
        bt_costs = {'thermoplastic': 1, 'thermoset': 12}
        tp_blade_demanded = 6
        tp_blade_supply = 12
        dissolution_available = {3: {'dissolution': False}}
        blade_type_capacities = {
            'Colorado': {'thermoplastic': 0, 'thermoset': 0},
            'California': {'thermoplastic': 0, 'thermoset': 0}}
        wpo_bt_list = []
        agent = random.choice(self.t_model_inst.schedule_dev.agents)
        test_tuple = agent.assign_wpo_blade_type(
            assigned_wpo, bt_costs, tp_blade_demanded, tp_blade_supply,
            dissolution_available, blade_type_capacities, wpo_bt_list)
        test = [test_tuple[0], test_tuple[1], test_tuple[2], test_tuple[3]]
        result = [16, {3: {'dissolution': False}, 1: {'dissolution': True},
                       2: {'dissolution': False}}, {
            'Colorado': {'thermoplastic': 4, 'thermoset': 0},
            'California': {'thermoplastic': 0, 'thermoset': 6}},
                  ['thermoplastic', 'thermoplastic']]
        self.assertCountEqual(test, result)

    def test_balance_demand_to_supply(self):
        """Test that demand-supply balance is respected"""
        wpo_blade_type = 'thermoplastic'
        bt_second_choice = 'thermoset'
        wpo_p_cap = 4
        tp_blade_demanded = 6
        tp_blade_supply = 12
        wpo_unique_id = 1
        wpo_state = 'Colorado'
        dissolution_available = {3: {'dissolution': False}}
        blade_type_capacities = {
            'Colorado': {'thermoplastic': 0, 'thermoset': 0},
            'California': {'thermoplastic': 0, 'thermoset': 0}}
        agent = random.choice(self.t_model_inst.schedule_dev.agents)
        test_tuple = agent.balance_demand_to_supply(
            wpo_blade_type, wpo_p_cap, tp_blade_demanded, tp_blade_supply,
            wpo_unique_id, wpo_state, dissolution_available,
            blade_type_capacities, bt_second_choice)
        test = [test_tuple[0], test_tuple[1], test_tuple[2]]
        result = [
            10, {3: {'dissolution': False}, 1: {'dissolution': True}}, {
                'Colorado': {'thermoplastic': 4, 'thermoset': 0},
                'California': {'thermoplastic': 0, 'thermoset': 0}}]
        self.assertCountEqual(test, result)

    def test_convert_blade_cost(self):
        """Test conversion"""
        bt_costs = {'1': 2, '3': 4}
        conversion_factor = 2
        agent = random.choice(self.t_model_inst.schedule_dev.agents)
        test = agent.convert_blade_cost(bt_costs, conversion_factor)
        result = {'1': 1, '3': 2}
        self.assertEqual(test, result)

    def test_update_agent_variables(self):
        """Function can't be formally tested here"""
        pass

    def test_step(self):
        """Test that the developer agents run steps without errors"""
        model = self.t_model_inst
        agent = random.choice(model.schedule_dev.agents)
        steps = 1
        agent.step()
        clock = agent.internal_clock
        self.assertEqual(steps, clock)
