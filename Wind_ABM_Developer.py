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


# TODO: lifetime extension:
#  Assign costs and revenue for lifetime extension

class Developer(Agent):
    def __init__(self, unique_id, model, **kwargs):
        super().__init__(unique_id, model)
        """
        Creation of new agent
        """
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.internal_clock = 0

        # TODO: replace mock-up values
        self.developer_type = list(self.model.developers.keys())[0]
        self.lifetime_extension_tr_cost = self.model.transport_repair
        self.lifetime_extension_cost = self.model.symetric_triang_distrib_draw(
            self.model.lifetime_extension_costs[0],
            self.model.lifetime_extension_costs[1])
        self.lifetime_extension_revenue = \
            self.model.symetric_triang_distrib_draw(
                self.model.lifetime_extension_revenues[0],
                self.model.lifetime_extension_revenues[1])
        self.model.variables_developers[self.developer_type].append(
            (self.unique_id, self.model.transport_repair,
             (self.lifetime_extension_cost - self.lifetime_extension_revenue)))

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
