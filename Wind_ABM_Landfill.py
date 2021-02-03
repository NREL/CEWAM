# -*- coding:utf-8 -*-
"""
Created on January 11 2021

@author Julien Walzberg - Julien.Walzberg@nrel.gov

Landfill - Circular Economy Wind Agent-based Model (CEWAM)
This module contains the Landfill class. Landfills make several
decisions, for instance, to accept Wind Blades or not.
"""

# Notes:
# Remove unused library imports


from mesa import Agent
import numpy as np
import random
from collections import OrderedDict
from scipy.stats import truncnorm
import operator
from math import *
import time


class Landfill(Agent):
    def __init__(self, unique_id, model, **kwargs):
        super().__init__(unique_id, model)
        """
        Creation of new agent
        """
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.internal_clock = 0
        self.landfill_type = list(self.model.landfills.keys())[0]
        self.landfill_state = self.mock_up_random_state(
            self.model.growth_rates)
        self.landfill_cost = self.model.landfill_costs[self.landfill_state]
        self.model.variables_landfills[self.landfill_type].append(
            (self.unique_id, self.landfill_state, self.landfill_cost))

    def mock_up(self):
        pass

    @staticmethod
    def mock_up_random_state(dic_to_shuffle):
        list_to_shuffle = list(dic_to_shuffle.keys())
        random.shuffle(list_to_shuffle)
        pick = list_to_shuffle[0]
        return pick

    def step(self):
        """
        Evolution of agent at each step. As Mesa is not built for having
        multiple scheduler, step needs to pass the global scheduler.
        """
        if self.internal_clock == self.model.clock:
            self.mock_up()
            self.internal_clock += 1
        else:
            pass
