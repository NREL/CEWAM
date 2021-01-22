# -*- coding:utf-8 -*-
"""
Created on December 31 2020

@author Julien Walzberg - Julien.Walzberg@nrel.gov

WindPlantOwner - Circular Economy Wind Agent-based Model (CEWAM)
This module contains the WindPlantOwner class. Wind plant owners make several
decisions, for instance, regarding EOL management.
"""

# Notes:
# Need to add adoption methods

# TODO:
#  1) Continue building model: Theory of Planned Behavior
#  2) Start other agents

from mesa import Agent


class WindPlantOwner(Agent):
    def __init__(self, unique_id, model, **kwargs):
        super().__init__(unique_id, model)
        """
        Creation of new agent
        """
        # Variables from inputs (value defined externally to the class):
        for key, value in kwargs.items():
            setattr(self, key, value)
        # Variables internal to the class -
        # Initial agents:
        if self.unique_id < self.model.uswtdb.shape[0]:
            self.p_cap = self.model.uswtdb.loc[self.unique_id]['p_cap']
            self.p_name = self.model.uswtdb.loc[self.unique_id]['p_name']
            self.p_year = self.model.uswtdb.loc[self.unique_id]['p_year']
            self.p_tnum = self.model.uswtdb.loc[self.unique_id]['p_tnum']
            self.t_state = self.model.uswtdb.loc[self.unique_id]['t_state']
            self.t_rd = self.model.uswtdb.loc[self.unique_id]['t_rd']
            self.t_cap = self.model.uswtdb.loc[self.unique_id]['t_cap']
            self.internal_clock = self.model.clock
        # Additional agents:
        else:
            self.t_state = self.model.list_agent_states[0]
            self.model.list_agent_states.pop(0)
            self.p_cap = \
                self.model.additional_cap[self.t_state] / \
                self.model.dict_agent_states[self.t_state]
            self.p_name = "".join(("Additional_agent_", self.t_state, "_",
                                  str(self.unique_id)))
            self.p_year = self.model.clock + \
                self.model.temporal_scope['simulation_start']
            self.p_tnum = round(
                self.model.uswtdb.groupby('t_state').mean().loc[
                    self.t_state]['p_tnum'])
            self.t_cap = self.p_cap / self.p_tnum
            self.t_rd = self.model.cap_to_diameter_model['coefficient'] * \
                self.t_cap**self.model.cap_to_diameter_model['power']
            self.internal_clock = self.model.clock + 1
        # All agents
        self.mass_conv_factor = self.compute_mass_conv_factor(
            self.t_rd, self.model.blade_size_to_mass_model['coefficient'],
            self.model.blade_size_to_mass_model['power'],
            self.model.blades_per_rotor, self.t_cap)
        self.growth_rate = self.model.growth_rates.get(self.t_state)
        self.p_cap_waste = self.p_cap
        self.waste = 0
        self.cum_waste = 0
        self.agent_attributes_counted = False

    @staticmethod
    def compute_mass_conv_factor(rotor_diameter, coefficient, power,
                                 blades_per_rotor, t_cap):
        """
        Compute a conversion factor to convert EOL volumes from MW to tons
        :param rotor_diameter: average rotor diameter in meters
        :param coefficient: coefficient of the power function
        :param power: power of the power function
        :param blades_per_rotor: number of blades in wind turbines' rotors
        :param t_cap: average turbine capacity
        :return: conversion factor in tons/MW
        """
        blade_radius = rotor_diameter / 2
        mass_blade = coefficient * blade_radius**power
        mass = mass_blade * blades_per_rotor
        conversion_factor = mass / t_cap
        return conversion_factor

    # TODO: the method below will need to be moved in the model module (to be
    #  accessible by different agent types)
    def subjective_norm(self):
        """
        Compute the subjective norms as measured by the proportion of agents
        tha have already adopted a given choice
        """
        # Bits of code for SN function:
        neighbors_nodes = self.model.grid_wpo.get_neighbors(
            self.pos, include_center=False)
        neighbors_nodes = [x for x in neighbors_nodes
                           if not self.model.grid_wpo.is_cell_empty(x)]
        print(neighbors_nodes)

    def update_agent_variables(self):
        """
        Update instance (agent) variables
        """
        self.waste = self.model.waste_generation(
            self.model.temporal_scope['simulation_start'], self.model.clock,
            self.p_year, self.p_cap_waste, self.model.average_lifetime,
            self.model.weibull_shape_factor)
        self.p_cap_waste -= self.waste
        self.cum_waste += self.waste

    def sum_agent_variable_once_or_every_step(self):
        """
        Sum the value of agent variables across all agents, once or every step
        of the simulation.
        """
        # Agents' attributes that should be counted once
        if not self.agent_attributes_counted:
            self.model.all_cap += self.p_cap
            self.model.states_cap[self.t_state] += self.p_cap
            self.agent_attributes_counted = True
        # Agents' attributes that should be counted every step
        self.model.all_waste += self.waste
        self.model.number_wpo_agent += 1

    def remove_agent(self):
        """
        Remove an agent once its (the wind turbine project) capacity is close
        to zero
        """
        if self.p_cap_waste < 1E-6:
            # self.model.grid_wpo._remove_agent(self, self.unique_id)
            self.model.grid_wpo.G.nodes[self.unique_id]["agent"].remove(self)
            self.model.schedule_wpo.remove(self)
            self.model.schedule.remove(self)

    def step(self):
        """
        Evolution of agent at each step. As Mesa is not built for having
        multiple scheduler, step needs to pass the global scheduler.
        """
        if self.internal_clock == self.model.clock:
            self.update_agent_variables()
            self.sum_agent_variable_once_or_every_step()
            self.remove_agent()
            self.internal_clock += 1
        else:
            pass
