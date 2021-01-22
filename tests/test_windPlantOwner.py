# -*- coding:utf-8 -*-
"""
Created on December 31 2020

@author Julien Walzberg - Julien.Walzberg@nrel.gov

Model - Circular Economy Wind Agent-based Model (CEWAM)
This module contains the model class that creates and activates agents. The
module also defines inputs (default values can be changed by user) and collect
outputs.
"""


from unittest import TestCase
from Wind_ABM_Model import WindABM
from Wind_ABM_WindPlantOwner import WindPlantOwner


# TODO: add tests
class TestWindPlantOwner(TestCase):
    def test_sum_agent_variable(self):
        """Function can't be formally tested here"""
        pass

    def test_wind_power_capacity_state_distribution(self):
        """Verify that capacities are distributed as should be within the US"""
        schedule = WindABM().schedule_wpo
        test_uswtdb = WindABM().uswtdb.drop(['p_name'], axis=1)
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
        unique_id = 0
        test_result = \
            WindPlantOwner(unique_id, WindABM()).compute_mass_conv_factor(
                rotor_diameter, coefficient, power, blades_per_rotor, t_cap)
        self.assertEqual(result, test_result)
