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
from mesa.time import RandomActivation
from mesa.space import NetworkGrid
from mesa import Agent
from mesa.time import BaseScheduler
import pandas as pd


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
                    test_sum += sum(a.p_cap)
            if test_sum == row['p_cap']:
                test_score.append(True)
            else:
                test_score.append(False)
            value.append(True)
        self.assertCountEqual(value, test_score)

    def test_cumulative_capacity_growth(self):
        """Verify that growth model behave as expected"""
        p_cap = [100.0, 50.0, 25.0]
        growth_rate = 0.1
        result = [x for x in p_cap]
        result.append(sum(p_cap) * growth_rate)
        WindPlantOwner(0, model=WindABM()).cumulative_capacity_growth(
            p_cap, growth_rate)
        self.assertCountEqual(result, p_cap)
