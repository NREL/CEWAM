# -*- coding:utf-8 -*-
"""
Created on January 26 2021

@author Julien Walzberg - Julien.Walzberg@nrel.gov

Test functions in Wind_ABM_Run
"""


from unittest import TestCase
from Wind_ABM_Run import *
import pandas as pd

# TODO: complete with unittest for latest results (e.g., verify that wastes in
#  all eol pathway tally to all waste reported in other global variable)


class TestWindABMRun(TestCase):
    @classmethod
    def setUpClass(cls):
        path = "C:/Users/jwalzber/PycharmProjects/WindABM/tests/results/"
        cls.number_run = 1
        cls.number_steps = 31
        test_model = WindABM(eol_pathways={
            "lifetime_extension": False, "dissolution": True,
            "pyrolysis": True, "mechanical_recycling": True,
            "cement_co_processing": True, "landfill": True})
        run_model(cls.number_run, cls.number_steps, test_model)
        cls.results_model = pd.read_csv(path + "Results_model_run_0.csv")

    def test_run_model_projected_capacity(self):
        """
        Test that run model provides expected cumulative installed
        capacity
        """
        test_cum_cap = round(
            self.results_model.loc[
                (self.number_steps - 1)]['Cumulative capacity (MW)'])
        cum_cap = 424728
        self.assertAlmostEqual(test_cum_cap, cum_cap, delta=100)

    def test_run_model_projected_waste(self):
        """Test that run model provides expected waste"""
        test_cum_waste = round(
            self.results_model.loc[
                (self.number_steps - 1)]['Cumulative waste (metric tons)'])
        cum_waste = 3936222
        self.assertAlmostEqual(test_cum_waste, cum_waste, delta=100)
