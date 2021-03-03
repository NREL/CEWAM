# -*- coding:utf-8 -*-
"""
Created on March 02 2021

@author Julien Walzberg - Julien.Walzberg@nrel.gov

Test functions in Wind_ABM_Manufacturer
"""

from unittest import TestCase
from Wind_ABM_Model import WindABM
import random


class TestManufacturer(TestCase):
    def setUp(self):
        self.t_model_inst = WindABM()

    def test_new_blade_design_adoption(self):
        """Function can't be formally tested here"""
        pass

    def test_lag_time_redesign(self):
        """Test that the Boolean is returned accordingly"""
        development_years1 = ['thermoplastic', 'thermoplastic', 'thermoset',
                              'thermoplastic']
        development_years2 = ['thermoset', 'thermoplastic', 'thermoplastic',
                              'thermoplastic']
        lag_time_tp_blade_dev = 3
        result = [False, True]
        agent = random.choice(self.t_model_inst.schedule_man.agents)
        test1 = agent.lag_time_redesign(development_years1,
                                        lag_time_tp_blade_dev)
        test2 = agent.lag_time_redesign(development_years2,
                                        lag_time_tp_blade_dev)
        test = [test1, test2]
        self.assertCountEqual(result, test)

    def test_quantity_tp_blade_produced(self):
        """Test that blade amount are properly computed"""
        bt_produced = {'thermoset': 1, 'thermoplastic': 0}
        producer_market_share = 0.5
        tp_production_share = 0.5
        additional_capacity = {'a': 2, 'b': 0, 'c': 2}
        agent = random.choice(self.t_model_inst.schedule_man.agents)
        test1 = agent.quantity_tp_blade_produced(
            True, bt_produced, producer_market_share, tp_production_share,
            additional_capacity).copy()
        test2 = agent.quantity_tp_blade_produced(
            False, bt_produced, producer_market_share, tp_production_share,
            additional_capacity)
        result = [{'thermoset': 1, 'thermoplastic': 1},
                  {'thermoset': 2, 'thermoplastic': 0}]
        test = [test1, test2]
        self.assertCountEqual(result, test)

    def test_manufacturing_waste(self):
        additional_capacity = {'a': 5, 'b': 5, 'c': 2}
        producer_market_share = 0.1
        wgt_avr_mass_c_fact = 2
        manufacturing_waste_ratio = {'d': 0.1, 'e': 0, 'f': 0.3}
        material_mass_fractions = {'d': 0.5, 'e': 0.2, 'f': 0.2}
        manufacturing_waste_q = {'d': 1, 'e': 0, 'f': 2}
        result = {'d': 1.12, 'e': 0, 'f': 2.144}
        agent = random.choice(self.t_model_inst.schedule_man.agents)
        test = agent.manufacturing_waste(
            additional_capacity, producer_market_share, wgt_avr_mass_c_fact,
            manufacturing_waste_ratio, material_mass_fractions,
            manufacturing_waste_q)
        self.assertEqual(result, test)

    def test_update_agent_variables(self):
        """Function can't be formally tested here"""
        pass

    def test_report_agent_variables(self):
        """Function can't be formally tested here"""
        pass

    def test_step(self):
        """Test that the wpo agents run steps without errors"""
        model = self.t_model_inst
        agent = random.choice(model.schedule_man.agents)
        steps = 1
        agent.step()
        clock = agent.internal_clock
        self.assertEqual(steps, clock)
