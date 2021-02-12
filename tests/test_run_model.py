# -*- coding:utf-8 -*-
"""
Created on January 26 2021

@author Julien Walzberg - Julien.Walzberg@nrel.gov

Test functions in Wind_ABM_Run
"""


from unittest import TestCase
from Wind_ABM_Run import *
import pandas as pd
import ast

# TODO: complete with unittest for latest results (e.g., verify that wastes in
#  all eol pathway tally to all waste reported in other global variable)


class TestWindABMRun(TestCase):
    @classmethod
    def setUpClass(cls):
        path = "C:/Users/jwalzber/PycharmProjects/WindABM/tests/results/"
        cls.number_run = 1
        cls.number_steps = 31
        test_parameters = {'eol_pathways': {
            "lifetime_extension": False, "dissolution": True,
            "pyrolysis": True, "mechanical_recycling": True,
            "cement_co_processing": True, "landfill": True}}
        run_model(cls.number_run, cls.number_steps, **test_parameters)
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

    def test_state_sum_tot_cap(self):
        """Test that the sum of capacities in all states is equal to all
        cumulative installed capacity during the simulation"""
        result = round(
            self.results_model.loc[
                (self.number_steps - 1)]['Cumulative capacity (MW)'])
        test_cap = \
            self.results_model.loc[
                (self.number_steps - 1)][
                'State cumulative capacity (MW)']
        test_cap = ast.literal_eval(test_cap)
        test_sum = 0
        for key, value in test_cap.items():
            test_sum += value
        test = test_sum
        self.assertAlmostEqual(result, test, delta=100)

    def test_run_model_projected_waste(self):
        """Test that run model provides expected waste"""
        test_cum_waste = round(
            self.results_model.loc[
                (self.number_steps - 1)]['Cumulative waste (metric tons)'])
        cum_waste = 3936222
        self.assertAlmostEqual(test_cum_waste, cum_waste, delta=100)

    def test_waste_eol_pathway_sum_tot_waste(self):
        """Test that the sum of waste in all eol pathway is equal to all
        waste generated during the simulation"""
        result = round(self.results_model.loc[
                (self.number_steps - 1)]['Cumulative waste (metric tons)'])
        test_waste = \
            self.results_model.loc[
                (self.number_steps - 1)][
                'State waste - eol pathways (metric tons)']
        test_waste = ast.literal_eval(test_waste)
        test_sum = 0
        for key, value in test_waste.items():
            for key2 in value.keys():
                test_sum += value[key2]
        test = test_sum
        self.assertAlmostEqual(result, test, delta=100)

    def test_waste_state_sum_tot_waste(self):
        """Test that the sum of waste in all states is equal to all
        waste generated during the simulation"""
        result = round(self.results_model.loc[
                (self.number_steps - 1)]['Cumulative waste (metric tons)'])
        test_waste = \
            self.results_model.loc[
                (self.number_steps - 1)][
                'State waste (metric tons)']
        test_waste = ast.literal_eval(test_waste)
        test_sum = 0
        for key, value in test_waste.items():
            test_sum += value
        test = test_sum
        self.assertAlmostEqual(result, test, delta=100)

    def test_run_model_projected_wind_project(self):
        """Test that run model provides expected number of agents"""
        test = self.results_model.loc[(self.number_steps - 1)][
            'Number wpo agents']
        result = 2181
        self.assertEqual(result, test)

    def test_wind_project_state_sum_tot(self):
        """Test that the sum of waste in all states is equal to all
        waste generated during the simulation"""
        result = self.results_model.loc[(self.number_steps - 1)][
            'Number wpo agents']
        test_wpo = \
            self.results_model.loc[
                (self.number_steps - 1)][
                'eol pathway adoption']
        test_waste = ast.literal_eval(test_wpo)
        test_sum = 0
        for key, value in test_waste.items():
            test_sum += value
        test = test_sum
        self.assertEqual(result, test)
