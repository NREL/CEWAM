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

# TODO:
#  1) use the "cement_facility_locations.csv" for the cement agents
#  C:\Users\jwalzber\Documents\Winter21\Wind_ABM\Modeling
#  2) Silica quarries location to map on cement factories (look up in USGS)
#  Will determined if cement factory accept waste



class Manufacturer(Agent):
    def __init__(self, unique_id, model, **kwargs):
        super().__init__(unique_id, model)
        """
        Creation of new agent
        """
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.internal_clock = 0

    def mock_up(self):
        pass

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
