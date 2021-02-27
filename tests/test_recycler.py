# -*- coding:utf-8 -*-
"""
Created on February 25 2021

@author Julien Walzberg - Julien.Walzberg@nrel.gov

Test functions in Wind_ABM_Recycler
"""

from unittest import TestCase
from Wind_ABM_Model import WindABM


class TestRecycler(TestCase):
    def setUp(self):
        self.t_model_inst = WindABM(eol_pathways={
            "lifetime_extension": True, "dissolution": True,
            "pyrolysis": True, "mechanical_recycling": True,
            "cement_co_processing": True, "landfill": True})

    def test_initial_recycling_quantity(self):
        self.fail()

    def test_learning_effect(self):
        self.fail()

    def test_learning_function(self):
        self.fail()

    def test_material_recovery(self):
        self.fail()

    def test_update_agent_variables(self):
        self.fail()

    def test_report_agent_variables(self):
        self.fail()

    def test_step(self):
        self.fail()
