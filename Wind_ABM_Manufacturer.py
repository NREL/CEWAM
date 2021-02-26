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

# TODO:
#  1) Silica quarries location to map on cement factories (look up in USGS)
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
        self.manufacturer_type = self.model.list_manufacturer_types.pop()
        self.yearly_tp_blade_manufactured = 0
        # Original equipment manufacturer only (wind_blade manufacturer type)
        if self.manufacturer_type == 'wind_blade':
            self.thermoset_blade_cost = \
                self.model.symetric_triang_distrib_draw(
                    self.model.blade_costs["thermoset"][0],
                    self.model.blade_costs["thermoset"][1])
            self.thermoplastic_blade_cost = self.model.blade_costs[
                "thermoplastic_rate"] * self.thermoset_blade_cost
            self.model.variables_manufacturers[self.manufacturer_type].append(
                (self.unique_id, self.thermoset_blade_cost,
                 self.thermoplastic_blade_cost))

    def mock_up(self):
        pass

    def update_agent_variables(self):
        """
        Update instance (agent) variables
        """
        # TODO: mock-up below to replace by real function
        if self.model.clock > 3 and self.manufacturer_type == 'wind_blade':
            self.yearly_tp_blade_manufactured = 1000

    def report_agent_variables(self):
        """
        Report instance (agent) variables
        """
        self.model.tp_blade_manufactured += \
            self.yearly_tp_blade_manufactured

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
