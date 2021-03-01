# -*- coding:utf-8 -*-
"""
Created on January 26 2021

@author Julien Walzberg - Julien.Walzberg@nrel.gov

Test functions in Wind_ABM_Run
"""

# TODO: some tests should verify the consequences of extreme scenarios. In
#  order to do that I can create several instance of the model class, run the
#  model and read the corresponding csv file and store in an instance variable
#  before moving to the next model instance


from unittest import TestCase
from Wind_ABM_Run import *
import pandas as pd
import ast


class TestWindABMRun(TestCase):
    @classmethod
    def setUpClass(cls):
        path = "C:/Users/jwalzber/PycharmProjects/WindABM/tests/results/"
        cls.number_run = 1
        cls.number_steps = 31
        test_parameters = {'eol_pathways': {
            "lifetime_extension": False, "dissolution": False,
            "pyrolysis": True, "mechanical_recycling": True,
            "cement_co_processing": True, "landfill": True}}
        test_model = WindABMRun(
            number_run=cls.number_run, number_steps=cls.number_steps,
            **test_parameters)
        test_model.run_model()
        cls.results_model = pd.read_csv(path + "Results_model_run_0.csv")
        test_parameters2 = {'eol_pathways': {
            "lifetime_extension": True, "dissolution": False,
            "pyrolysis": True, "mechanical_recycling": True,
            "cement_co_processing": True, "landfill": True},
            "attitude_eol_parameters": {
                'mean': 0.9, 'standard_deviation': 0.1, 'min': 0, 'max': 1}}
        test_model2 = WindABMRun(
            number_run=cls.number_run, number_steps=cls.number_steps,
            **test_parameters2)
        test_model2.run_model()
        cls.results_model2 = pd.read_csv(path + "Results_model_run_0.csv")

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
        result = 2178
        self.assertAlmostEqual(result, test, delta=20)

    def test_wind_project_state_sum_tot(self):
        """Test that the sum of wpo that have adopted different eol pathways
        is equal to all wpo during the simulation"""
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
        self.assertAlmostEqual(result, test, delta=20)

    def test_state_blade_type_sum_tot_cap(self):
        """Test that the sum of capacities in all states for both blade type
        is equal to all cumulative installed capacity during the simulation"""
        result = round(
            self.results_model.loc[
                (self.number_steps - 1)]['Cumulative capacity (MW)'] -
            self.results_model.loc[1]['Cumulative capacity (MW)'])
        test_cap = \
            self.results_model.loc[
                (self.number_steps - 1)]['Blade type adoption (MW)']
        test_cap = ast.literal_eval(test_cap)
        test_sum = 0
        for key, value in test_cap.items():
            for key2 in value.keys():
                test_sum += value[key2]
        test = test_sum
        self.assertAlmostEqual(result, test, delta=100)

    def test_average_recycling_costs(self):
        """Test that the average recycling costs in each eol pathway are equal
        to the mean of the range in the model's inputs for each eol pathway"""
        test_cap = self.results_model.loc[1][
            'Average recycling costs ($/metric ton)']
        test_cap = ast.literal_eval(test_cap)
        results = {
            'lifetime_extension': 0, 'dissolution': 0, 'pyrolysis': 415.25,
            'mechanical_recycling': 272.25, 'cement_co_processing': 0,
            'landfill': 0}
        deltas = {
            'lifetime_extension': 0.1, 'dissolution': 0.1, 'pyrolysis': 50,
            'mechanical_recycling': 50, 'cement_co_processing': 0.1,
            'landfill': 0.1}
        for key in test_cap.keys():
            test = test_cap[key]
            result = results[key]
            delta = deltas[key]
            self.assertAlmostEqual(result, test, delta=delta)

    def test_recovered_materials(self):
        """Test that the amounts of recovered materials sum up to the amount of
        recycled blades in each eol pathway"""
        test_cap = self.results_model2.loc[(self.number_steps - 1)][
            'Recovered materials (metric tons)']
        results = self.results_model2.loc[(self.number_steps - 1)][
            'State waste - eol pathways (metric tons)']
        test_cap = ast.literal_eval(test_cap)
        results = ast.literal_eval(results)
        sum_states = {'lifetime_extension': 0, 'dissolution': 0,
                      'pyrolysis': 0, 'mechanical_recycling': 0,
                      'cement_co_processing': 0, 'landfill': 0}
        for value in results.values():
            for key2, value2 in value.items():
                sum_states[key2] += value2
        [sum_states.pop(key) for key in ['lifetime_extension', 'landfill']]
        blade_mass_fractions = {
            "steel": 0.05, "plastic": 0.09, "resin": 0.30,
            "glass_fiber": 0.56}
        rec_recovery_fractions = {
            "dissolution": {"steel": 1, "plastic": 1, "resin": 1,
                            "glass_fiber": 1},
            "pyrolysis": {"steel": 1, "plastic": 0, "resin": 0,
                          "glass_fiber": 0.5},
            "mechanical_recycling": {"steel": 1, "plastic": 1,
                                     "resin": 1, "glass_fiber": 1},
            "cement_co_processing": {"steel": 1, "plastic": 0,
                                     "resin": 0, "glass_fiber": 1}}
        material_recycled = {'steel': 0, 'plastic': 0, 'resin': 0,
                             'glass_fiber': 0}
        for key, value in sum_states.items():
            mass_recycled = value
            for key2, value2 in blade_mass_fractions.items():
                material_recycled[key2] += mass_recycled * value2 * \
                                           rec_recovery_fractions[key][key2]
        for key, value in test_cap.items():
            test_cap[key] = round(value)
            material_recycled[key] = round(material_recycled[key])
        self.assertEqual(test_cap, material_recycled)
