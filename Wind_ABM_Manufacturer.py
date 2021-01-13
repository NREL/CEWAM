# -*- coding:utf-8 -*-
"""
Created on December 31 2020

@author Julien Walzberg - Julien.Walzberg@nrel.gov

Manufacturer - Circular Economy Wind Agent-based Model (CEWAM)
This module contains the Manufacturer class. Manufacturers make several
decisions, for instance, regarding the design of wind blades.
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


class Manufacturer(Agent):
    def __init__(self, unique_id, model, **kwargs):
        super().__init__(unique_id, model)
        """
        Creation of new agent
        """
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.internal_clock = 0

    def give_unit(self):
        neighbors_nodes = self.model.grid_man.get_neighbors(
            self.pos, include_center=False)
        obtainer = random.choice(neighbors_nodes)
        if self.unit > 0:
            self.unit -= 1
            # for agent in self.model.schedule.agents:
            # if agent.unique_id == obtainer:
            # agent.unit += 1
        # print(self.unique_id)

    def step(self):
        """
        Evolution of agent at each step. As Mesa is not built for having
        multiple scheduler, step needs to pass the global scheduler.
        """
        if self.internal_clock == self.model.clock:
            self.give_unit()
            self.internal_clock += 1
        else:
            pass
