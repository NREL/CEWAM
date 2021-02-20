# -*- coding:utf-8 -*-
"""
Created on January 11 2021

@author Julien Walzberg - Julien.Walzberg@nrel.gov

Developer - Circular Economy Wind Agent-based Model (CEWAM)
This module contains the Developer class. Developers make several
decisions, for instance, what type blade to choose for a given wind turbine.
"""


from mesa import Agent


# TODO: lifetime extension:
#  1) Assign costs and revenue for lifetime extension
#  2) set up projected capacities instead of wpo
#  3) use doi:10.1088/1757-899X/429/1/012024 to write about green procurement

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
        self.le_feasibility = self.model.le_feasibility
        self.lifetime_extension_years = \
            self.model.symetric_triang_distrib_draw(
                self.model.lifetime_extension_years[0],
                self.model.lifetime_extension_years[1])
        self.model.le_characteristics.append((self.le_feasibility,
                                              self.lifetime_extension_years))

    def mock_up(self):
        pass

    def install_additional_cap(self):
        if not self.model.all_additional_cap_installed:
            self.model.additional_cap = self.model.cumulative_capacity_growth(
                self.model.states_cap, self.model.growth_rates,
                self.model.additional_cap)
            self.model.all_additional_cap_installed = True

    def update_agent_variables(self):
        """
        Update instance (agent) variables
        """
        self.lifetime_extension_years = \
            self.model.symetric_triang_distrib_draw(
                self.model.lifetime_extension_years[0],
                self.model.lifetime_extension_years[1])
        self.model.le_characteristics.append((self.le_feasibility,
                                              self.lifetime_extension_years))

    def step(self):
        """
        Evolution of agent at each step. As Mesa is not built for having
        multiple scheduler, step needs to pass the global scheduler.
        """
        if self.internal_clock == self.model.clock:
            self.mock_up()
            self.install_additional_cap()
            self.update_agent_variables()
            self.internal_clock += 1
        else:
            pass
