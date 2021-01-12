# -*- coding:utf-8 -*-
"""
Created on December 31 2020

@author Julien Walzberg - Julien.Walzberg@nrel.gov

WindPlantOwner - Circular Economy Wind Agent-based Model (CEWAM)
This module contains the WindPlantOwner class. Wind plant owners make several
decisions, for instance, regarding EOL management.
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


class WindPlantOwner(Agent):
    def __init__(self, unique_id, model, **kwargs):
        super().__init__(unique_id, model)
        """
        Creation of new agent
        """
        for key, value in kwargs.items():
            setattr(self, key, value)

    def give_unit(self):
        neighbors_nodes = self.model.grid_wpo.get_neighbors(self.pos,
                                                        include_center=False)
        obtainer = random.choice(neighbors_nodes)
        if self.unit > 0:
            self.unit -= 1
            # for agent in self.model.schedule.agents:
            # if agent.unique_id == obtainer:
            # agent.unit += 1
        # print(self.unique_id)

    def sum_agent_variable(self):
        """
        Sum the value of agent variables across all agents
        """
        self.model.all_agents_unit += self.unit

    def step(self):
        """
        Evolution of agent at each step
        """
        self.give_unit()
        self.sum_agent_variable()
