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
        # Variables from inputs (value defined externally to the class):
        for key, value in kwargs.items():
            setattr(self, key, value)
        # Variables internal to the class:
        self.internal_clock = self.model.clock
        self.p_cap = self.model.uswtdb.loc[self.unique_id]['p_cap']
        self.p_name = self.model.uswtdb.loc[self.unique_id]['p_name']
        self.p_year = self.model.uswtdb.loc[self.unique_id]['p_year']
        self.p_tnum = self.model.uswtdb.loc[self.unique_id]['p_tnum']
        self.p_cap_waste = self.p_cap.copy()
        self.t_state = self.model.uswtdb.loc[self.unique_id]['t_state']
        self.t_rd = self.model.uswtdb.loc[self.unique_id]['t_rd']
        self.t_cap = self.model.uswtdb.loc[self.unique_id]['t_cap']
        self.mass_conv_factor = self.compute_mass_conv_factor(
            self.t_rd, self.model.blade_size_to_mass_model['coefficient'],
            self.model.blade_size_to_mass_model['power'], self.t_cap)
        self.growth_rate = self.model.growth_rates.get(self.t_state)
        self.waste = 0

    # TODO:
    #  1) add and remove agents to the network
    #  2) Continue building model: Theory of Planned Behavior

    @staticmethod
    def compute_mass_conv_factor(rotor_diameter, coefficient, power, t_cap):
        """
        Compute a conversion factor to convert EOL volumes from MW to tons
        :param rotor_diameter: average rotor diameter in meters
        :param coefficient: coefficient of the power function
        :param power: power of the power function
        :param t_cap: average turbine capacity
        :return: conversion factor in tons/MW
        """
        blade_radius = rotor_diameter / 2
        mass = coefficient * blade_radius**power
        conversion_factor = mass / t_cap
        return conversion_factor

    def update_agent_variables(self):
        """Update instance (agent) variables"""
        self.waste = self.model.waste_generation(
            self.p_year, self.p_cap_waste, self.model.average_lifetime,
            self.model.weibull_shape_factor)
        self.p_cap_waste -= self.waste
        self.p_cap = self.model.cumulative_capacity_growth(
            self.p_cap, self.growth_rate)

    def sum_agent_variable(self):
        """
        Sum the value of agent variables across all agents
        """
        self.model.all_cap += self.p_cap
        self.model.all_waste += self.p_cap_waste

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
