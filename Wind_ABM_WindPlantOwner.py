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
# For now we assume the number of project stays constant (but the installed
# capacity grow). If the assumption is remove the number of agents would grow
# up to about 4000 (100 wind project per year if looking at the 2000-2015
# number of installations).


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

        self.internal_clock = self.model.clock
        self.p_cap = [0] * int(self.model.uswtdb['p_year'].max() -
                               self.model.uswtdb['p_year'].min() + 1)
        self.p_name = self.model.uswtdb.loc[self.unique_id]['p_name']
        self.p_year = self.model.uswtdb.loc[self.unique_id]['p_year']
        self.p_tnum = self.model.uswtdb.loc[self.unique_id]['p_tnum']
        self.p_cap[int(self.p_year -
                       self.model.uswtdb['p_year'].min())] = \
            self.model.uswtdb.loc[self.unique_id]['p_cap']  # in MW
        self.p_cap_waste = self.p_cap.copy()
        self.t_state = self.model.uswtdb.loc[self.unique_id]['t_state']
        self.growth_rate = self.model.growth_rates.get(self.t_state)
        self.cum_cap = sum(self.p_cap)
        self.waste = []
        self.cum_waste = 0

    def update_agent_variables(self):
        """Update instance (agent) variables"""
        self.waste = self.model.waste_generation(
            self.model.uswtdb['p_year'], self.p_cap_waste,
            self.model.average_lifetime, self.model.weibull_shape_factor)
        self.p_cap_waste = self.model.subtract_lists(
            self.p_cap_waste, self.waste)
        self.p_cap = self.model.cumulative_capacity_growth(
            self.p_cap, self.growth_rate)
        self.p_cap_waste[-1] = self.p_cap[-1]
        self.cum_cap = sum(self.p_cap)
        self.cum_waste = sum(self.waste)

    def sum_agent_variable(self):
        """
        Sum the value of agent variables across all agents
        """
        self.model.all_cum_cap += self.cum_cap
        self.model.all_cum_waste += self.cum_waste

    def step(self):
        """
        Evolution of agent at each step. As Mesa is not built for having
        multiple scheduler, step needs to pass the global scheduler.
        """
        if self.internal_clock == self.model.clock:
            self.update_agent_variables()
            self.sum_agent_variable()
            self.internal_clock += 1
        else:
            pass
