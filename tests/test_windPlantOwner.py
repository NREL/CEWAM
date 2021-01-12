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
