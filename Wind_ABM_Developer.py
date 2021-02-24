# -*- coding:utf-8 -*-
"""
Created on January 11 2021

@author Julien Walzberg - Julien.Walzberg@nrel.gov

Developer - Circular Economy Wind Agent-based Model (CEWAM)
This module contains the Developer class. Developers make several
decisions, for instance, what type blade to choose for a given wind turbine.
"""


from mesa import Agent
import random


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
        self.blade_type = self.model.list_init_blade_types.pop()
        self.bt_second_choice = random.choice(self.model.filter_list(
            self.model.list_init_bt_second_choice, self.blade_type))
        self.bt_att_level_ce = self.model.trunc_normal_distrib_draw(
            (self.model.attitude_bt_parameters['min'] -
             self.model.attitude_bt_parameters['mean']) /
            self.model.attitude_bt_parameters['standard_deviation'],
            (self.model.attitude_bt_parameters['max'] -
             self.model.attitude_bt_parameters['mean']) /
            self.model.attitude_bt_parameters['standard_deviation'],
            self.model.attitude_bt_parameters['mean'],
            self.model.attitude_bt_parameters['standard_deviation'])
        self.bt_att_level_conv = self.model.trunc_normal_distrib_draw(
            (self.model.attitude_bt_parameters['min'] -
             self.model.attitude_bt_parameters['mean']) /
            self.model.attitude_bt_parameters['standard_deviation'],
            (self.model.attitude_bt_parameters['max'] -
             self.model.attitude_bt_parameters['mean']) /
            self.model.attitude_bt_parameters['standard_deviation'],
            (self.model.attitude_bt_parameters['max'] -
             self.model.attitude_bt_parameters['mean']),
            self.model.attitude_bt_parameters['standard_deviation'])
        self.dev_blade_types = self.model.blade_types.copy()
        self.assigned_wpo = []
        # List of tuples: x=man.unique_id, y=man.thermoset_blade_cost,
        # z=man.thermoplastic_blade_cost
        self.assigned_man = random.choice(
            self.model.assign_agents_to_each_other(
                self.model.variables_manufacturers['wind_blade'],
                sum(self.model.developers.values()),
                self.model.manufacturers['wind_blade'],
                [], False))
        self.bt_costs = self.model.initial_dic_from_key_list(
            self.model.blade_types, 0)
        self.bt_costs['thermoset'] = self.assigned_man[1]
        self.bt_costs['thermoplastic'] = self.assigned_man[2]
        self.state_dev = self.model.random_pick_dic_key(
            self.model.growth_rates)
        self.bt_barriers = self.model.initial_dic_from_key_list(
            self.model.blade_types.keys(), 0)

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
        # List of tuples: x=wpo.unique_id, y=wpo.blade_mass_conv_factor
        self.assigned_wpo = self.model.assign_agents_to_each_other(
            self.model.variables_additional_wpo,
            sum(self.model.developers.values()), self.model.p_install_growth,
            self.assigned_wpo, True)
        # TODO: uncomment when ready
        self.blade_type, self.bt_second_choice = \
            self.model.theory_planned_behavior_model(
                self.model.tpb_bt_coeff, self.bt_att_level_ce,
                self.bt_att_level_conv, self.dev_blade_types,
                self.model.choices_circularity, self.model.grid_dev,
                'blade_type', self.pos, self.bt_costs, self.bt_barriers,
                self.state_dev, self.model.regulations_enacted)

    def step(self):
        """
        Evolution of agent at each step. As Mesa is not built for having
        multiple scheduler, step needs to pass the global scheduler.
        """
        if self.internal_clock == self.model.clock:
            self.install_additional_cap()
            self.update_agent_variables()
            self.internal_clock += 1
        else:
            pass
