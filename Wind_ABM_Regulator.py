# -*- coding:utf-8 -*-
"""
Created on January 11 2021

@author Julien Walzberg - Julien.Walzberg@nrel.gov

Regulator - Circular Economy Wind Agent-based Model (CEWAM)
This module contains the Regulator class. Regulators make several
decisions, for instance, to ban some landfills from accepting blades.
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


class Regulator(Agent):
    def __init__(self, unique_id, model, **kwargs):
        super().__init__(unique_id, model)
        """
        Creation of new agent
        """
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.internal_clock = 0

        # TODO: replace mock-up values below
        self.regulator_state = self.model.regulator_states_list.pop()
        self.regulation_enacted = self.model.initial_dic_from_key_list(
            self.model.eol_pathways, False)

    def mock_up(self):
        pass

    def update_agent_variables(self):
        """
        Update instance (agent) variables
        """
        # TODO: build regulation enacting
        self.regulation_enacted = self.model.initial_dic_from_key_list(
            self.model.eol_pathways, False)

    def report_agent_variables(self):
        """
        Report instance (agent) variables
        """
        for key in self.regulation_enacted.keys():
            self.model.regulations_enacted[key][self.regulator_state] = \
                self.regulation_enacted[key]

    def step(self):
        """
        Evolution of agent at each step. As Mesa is not built for having
        multiple scheduler, step needs to pass the global scheduler.
        """
        if self.internal_clock == self.model.clock:
            self.mock_up()
            self.update_agent_variables()
            self.report_agent_variables()
            self.internal_clock += 1
        else:
            pass
