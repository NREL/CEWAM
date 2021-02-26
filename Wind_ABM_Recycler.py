# -*- coding:utf-8 -*-
"""
Created on January 11 2021

@author Julien Walzberg - Julien.Walzberg@nrel.gov

Recycler - Circular Economy Wind Agent-based Model (CEWAM)
This module contains the Recycler class. Recyclers make several
decisions, for instance, what type of recycling to perform.
"""

# Notes:
# Remove unused library imports


from mesa import Agent


class Recycler(Agent):
    def __init__(self, unique_id, model, **kwargs):
        super().__init__(unique_id, model)
        """
        Creation of new agent
        """
        for key, value in kwargs.items():
            setattr(self, key, value)
        # Variables internal to the class -
        self.internal_clock = 0
        self.recycler_type = self.model.list_recycler_types.pop()
        # TODO: uncomment below and delete other recycler_state lines
        # self.recycler_state = self.model.assign_elements_from_list(
        #    self.model.recyclers_states[self.recycler_type], True)
        self.recycler_state = self.model.assign_elements_from_list(
            list(self.model.growth_rates.keys()), False)
        self.init_recycler_cost = self.model.symetric_triang_distrib_draw(
            self.model.rec_processes_costs[self.recycler_type][0],
            self.model.rec_processes_costs[self.recycler_type][1])
        self.recycler_revenue = self.model.symetric_triang_distrib_draw(
            self.model.rec_processes_revenues[self.recycler_type][0],
            self.model.rec_processes_revenues[self.recycler_type][1])
        self.model.variables_recyclers[self.recycler_type].append(
            (self.unique_id, self.recycler_state, (self.init_recycler_cost -
                                                   self.recycler_revenue)))
        self.recycler_cost = 0
        self.init_recycled_quantity = 0
        self.recycled_quantity = 0
        self.model.waste_rec_land[self.unique_id] = 0

    def initial_recycling_quantity(self, clock, unique_id, simulation_start,
                                   waste_rec_land):
        if (clock + simulation_start) == simulation_start:
            self.init_recycled_quantity = waste_rec_land[unique_id]

    def update_agent_variables(self):
        """
        Update instance (agent) variables
        """
        # TODO: build learning effect function and update recycler costs
        #  instead of having self.init_recycler_cost
        self.initial_recycling_quantity(
            self.model.clock, self.unique_id,
            self.model.temporal_scope['simulation_start'],
            self.model.waste_rec_land)
        self.recycled_quantity = self.model.waste_rec_land[self.unique_id]
        self.recycler_cost = self.init_recycler_cost
        # TODO continue HERE: learning effect function

    def report_agent_variables(self):
        """
        Report instance (agent) variables
        """
        self.model.variables_recyclers[self.recycler_type].append(
            (self.unique_id, self.recycler_state, self.recycler_cost))

    def step(self):
        """
        Evolution of agent at each step. As Mesa is not built for having
        multiple scheduler, step needs to pass the global scheduler.
        """
        if self.internal_clock == self.model.clock:
            self.update_agent_variables()
            self.report_agent_variables()
            self.internal_clock += 1
        else:
            pass
