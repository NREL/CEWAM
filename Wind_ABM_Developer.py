# -*- coding:utf-8 -*-
"""
Created on January 11 2021

@author Julien Walzberg - Julien.Walzberg@nrel.gov

Developer - Circular Economy Wind Agent-based Model (CEWAM)
This module contains the Developer class. Developers make several
decisions, for instance, what type blade to choose for a given wind turbine.
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


class Developer(Agent):
    def __init__(self, unique_id, model, **kwargs):
        super().__init__(unique_id, model)
        """
        Creation of new agent
        """
        for key, value in kwargs.items():
            setattr(self, key, value)

    def give_unit(self):
        neighbors_nodes = self.model.grid_dev.get_neighbors(self.pos,
                                                        include_center=False)
        obtainer = random.choice(neighbors_nodes)
        if self.unit > 0:
            self.unit -= 1
            # for agent in self.model.schedule.agents:
            # if agent.unique_id == obtainer:
            # agent.unit += 1
        # print(self.unique_id)

    def step(self):
        """
        Evolution of agent at each step
        """
        self.give_unit()
