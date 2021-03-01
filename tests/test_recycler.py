# -*- coding:utf-8 -*-
"""
Created on February 25 2021

@author Julien Walzberg - Julien.Walzberg@nrel.gov

Test functions in Wind_ABM_Recycler
"""

from unittest import TestCase
from Wind_ABM_Model import WindABM
import random


class TestRecycler(TestCase):
    def setUp(self):
        self.t_model_inst = WindABM()

    def test_initial_recycling_quantity(self):
        """Function can't be formally tested here"""
        pass

    def test_learning_effect(self):
        """
        Test that the learning function compute the recycling cost correctly
        only when the costs are actually decreased, otherwise it should
        return current costs
        """
        original_volume = 1
        volume = 4
        original_cost = 1
        current_cost = 1
        learning_parameter = -0.5
        agent = random.choice(self.t_model_inst.schedule_rec.agents)
        test1 = agent.learning_effect(
            original_volume, volume, original_cost, current_cost,
            learning_parameter)
        test2 = agent.learning_effect(
            original_volume, volume/8, original_cost, current_cost,
            learning_parameter)
        test = [test1, test2]
        result = [0.5, 1]
        self.assertCountEqual(test, result)

    def test_learning_function(self):
        """Test the learning function"""
        original_volume = 4
        volume = 8
        original_cost = 4
        learning_parameter = -2
        agent = random.choice(self.t_model_inst.schedule_rec.agents)
        test = agent.learning_function(original_volume, volume, original_cost,
                                       learning_parameter)
        result = 1
        self.assertEqual(test, result)

    def test_material_recovery(self):
        """Test that the amount of recovered materials is computed correctly"""
        recycled_quantity = 2
        blade_mass_fractions = {'a': 0.2, 'b': 0.3, 'c': 0.3}
        rec_recovery_fractions = {'test': {'a': 0.5, 'b': 1, 'c': 0}}
        recycler_type = 'test'
        recovered_materials = {'a': 0, 'b': 1, 'c': 0.5}
        agent = random.choice(self.t_model_inst.schedule_rec.agents)
        test = agent.material_recovery(
            recycled_quantity, blade_mass_fractions, rec_recovery_fractions,
            recycler_type, recovered_materials)
        result = {'a': 0.2, 'b': 1.6, 'c': 0.5}
        self.assertEqual(test, result)

    def test_update_agent_variables(self):
        """Function can't be formally tested here"""
        pass

    def test_report_agent_variables(self):
        """Function can't be formally tested here"""
        pass

    def test_step(self):
        """Test that the recycler agents run steps without errors"""
        model = self.t_model_inst
        agent = random.choice(model.schedule_rec.agents)
        steps = 1
        agent.step()
        clock = agent.internal_clock
        self.assertEqual(steps, clock)
