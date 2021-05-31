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


class Developer(Agent):
    def __init__(self, unique_id, model, **kwargs):
        super().__init__(unique_id, model)
        """
        Creation of new agent
        """
        for key, value in kwargs.items():
            setattr(self, key, value)
        # Variables internal to the class -
        self.internal_clock = self.model.clock
        self.developer_type = list(self.model.developers.keys())[0]
        self.lifetime_extension_tr_cost = self.model.transport_repair
        self.lifetime_extension_cost = self.model.symetric_triang_distrib_draw(
            self.model.lifetime_extension_costs[0],
            self.model.lifetime_extension_costs[1])
        self.lifetime_extension_revenue = \
            self.model.symetric_triang_distrib_draw(
                self.model.lifetime_extension_revenues[0],
                self.model.lifetime_extension_revenues[1])
        # costs and revenues are seen by wind plant owners
        self.model.variables_developers[self.developer_type].append(
            (self.unique_id, self.model.transport_repair,
             self.lifetime_extension_cost - self.lifetime_extension_revenue,
             self.lifetime_extension_cost, self.lifetime_extension_revenue))
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
        self.wpo_bt_list = []
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
             (self.model.attitude_bt_parameters['max'] -
              self.model.attitude_bt_parameters['mean'])) /
            self.model.attitude_bt_parameters['standard_deviation'],
            (self.model.attitude_bt_parameters['max'] -
             (self.model.attitude_bt_parameters['max'] -
              self.model.attitude_bt_parameters['mean'])) /
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
                self.model.p_install_growth, [], False))
        self.bt_costs = self.model.initial_dic_from_key_list(
            self.model.blade_types, 0)
        self.bt_costs['thermoset'] = self.assigned_man[1]
        self.bt_costs['thermoplastic'] = self.assigned_man[2]
        self.state_dev = self.model.random_pick_dic_key(
            self.model.growth_rates)
        self.bt_barriers = self.model.initial_dic_from_key_list(
            self.model.blade_types.keys(), 0)
        self.model.average_eol_costs[self.developer_type] += \
            self.lifetime_extension_cost / \
            self.model.developers[self.developer_type]

    def install_additional_cap(self):
        """Determine additional capacity in each state"""
        if not self.model.all_additional_cap_installed:
            self.model.additional_cap = self.model.cumulative_capacity_growth(
                self.model.states_cap, self.model.growth_rates,
                self.model.additional_cap)
            self.model.all_additional_cap_installed = True

    def assign_wpo_blade_type(self, assigned_wpo, bt_costs, tp_blade_demanded,
                              tp_blade_supply, dissolution_available,
                              blade_type_capacities, wpo_bt_list,
                              total_blade_costs):
        """
        Assign wpo blade type (thermoplastic or thermoset) to wpo depending on
        the TPB
        :param assigned_wpo: list of assigned wpo and some of their variables
        (unique id, blade to mass conversion factor, installed capacity)
        :param bt_costs: costs of thermoplastic and thermoset blades
        :param tp_blade_demanded: thermoplastic blades installed by developers
        (MW) up to the current developer
        :param tp_blade_supply: number of blade supplied by manufacturer (MW)
        :param dissolution_available: dictionary of boolean to indicate wpo
        have thermoplastic blades and thus can opt for dissolution
        :param blade_type_capacities: model reporter of new installed capacity
        by blade type in each state
        :param wpo_bt_list: list of blade type from each wpo
        :param total_blade_costs: dictionary reporting blade costs ($)
        :return: the blade demanded up to (and including) current developer,
        dictionary with boolean to indicate wpo have thermoplastic blades, the
        new installed capacity by blade type in each state, and a list of blade
        type from each wpo
        """
        for i in range(len(assigned_wpo)):
            wpo_unique_id = assigned_wpo[i][0]
            wpo_blade_mass_conv_factor = assigned_wpo[i][1]
            wpo_p_cap = assigned_wpo[i][2]
            wpo_t_state = assigned_wpo[i][3]
            wpo_mass_conv_factor = assigned_wpo[i][4]
            converted_bt_costs = self.convert_blade_cost(
                bt_costs, wpo_blade_mass_conv_factor)
            wpo_blade_type, bt_second_choice = \
                self.model.theory_planned_behavior_model(
                    self.model.tpb_bt_coeff, self.bt_att_level_ce,
                    self.bt_att_level_conv, self.dev_blade_types,
                    self.model.choices_circularity, self.model.grid_dev,
                    'blade_type', self.pos, converted_bt_costs,
                    self.bt_barriers, self.state_dev,
                    self.model.regulations_enacted)
            tp_blade_demanded, dissolution_available, blade_type_capacities, \
                total_blade_costs = self.balance_demand_to_supply(
                    wpo_blade_type, wpo_p_cap, tp_blade_demanded,
                    tp_blade_supply, wpo_unique_id, wpo_t_state,
                    dissolution_available, blade_type_capacities,
                    bt_second_choice, wpo_mass_conv_factor, total_blade_costs,
                    converted_bt_costs)
            wpo_bt_list.append(wpo_blade_type)
        return tp_blade_demanded, dissolution_available, \
            blade_type_capacities, wpo_bt_list, total_blade_costs

    # TODO: modify unittest
    @staticmethod
    def balance_demand_to_supply(wpo_blade_type, wpo_p_cap, tp_blade_demanded,
                                 tp_blade_supply, wpo_unique_id, wpo_t_state,
                                 dissolution_available, blade_type_capacities,
                                 bt_second_choice, wpo_mass_conv_factor,
                                 total_blade_costs, converted_bt_costs):
        """
        Function to balance demand of blades from developers to supply from
        manufacturers, dissolution is set to True if the developer adopt a
        thermoplastic design and the demand-supply balance is maintained and
        to False otherwise
        :param wpo_blade_type: type of blade chosen according to TPB
        :param wpo_p_cap: wpo project capacity
        :param tp_blade_demanded: thermoplastic blades installed by developers
        (MW) up to the current developer
        :param tp_blade_supply: number of blade supplied by manufacturer (MW)
        :param wpo_unique_id: unique id of wpo
        :param wpo_t_state: state of the wpo
        :param dissolution_available: nested dictionary with first key being
        the wpo unique id and second key being the dissolution process
        :param blade_type_capacities: model reporter of new installed capacity
        by blade type in each state
        :param bt_second_choice: second highest score choice in the TPB, which
        replaces wpo_blade_type if supply of thermoplastic blade is limited
        :param wpo_mass_conv_factor: wpo conversion factor in ton/MW
        :param total_blade_costs: dictionary reporting blade costs ($)
        :param converted_bt_costs: costs of each blade type ($/ton)
        :return: the blade demanded up to (and including) current developer,
        nested dictionary dissolution_available, and the new installed capacity
        by blade type in each state
        """
        if wpo_blade_type == 'thermoplastic':
            tp_blade_demanded += wpo_p_cap
            if tp_blade_demanded < tp_blade_supply:
                dissolution_available[wpo_unique_id] = {
                    'dissolution': True}
                blade_type_capacities[wpo_t_state][wpo_blade_type] += wpo_p_cap
                total_blade_costs[wpo_blade_type] += \
                    wpo_p_cap * wpo_mass_conv_factor * \
                    converted_bt_costs[wpo_blade_type]
            else:
                dissolution_available[wpo_unique_id] = {
                    'dissolution': False}
                blade_type_capacities[wpo_t_state][bt_second_choice] += \
                    wpo_p_cap
                total_blade_costs[bt_second_choice] += \
                    wpo_p_cap * wpo_mass_conv_factor * \
                    converted_bt_costs[bt_second_choice]
        else:
            dissolution_available[wpo_unique_id] = {
                'dissolution': False}
            blade_type_capacities[wpo_t_state][wpo_blade_type] += wpo_p_cap
            total_blade_costs[wpo_blade_type] += \
                wpo_p_cap * wpo_mass_conv_factor * \
                converted_bt_costs[wpo_blade_type]
        return tp_blade_demanded, dissolution_available, \
            blade_type_capacities, total_blade_costs

    @staticmethod
    def convert_blade_cost(bt_costs, conversion_factor):
        """
        Convert blade costs in $/blade to $/ton depending on wpo
        attributes
        :param bt_costs: Dictionary with blade costs in $/blade
        :param conversion_factor: wpo conversion factor computed based on the
        average rotor diameter and turbine capacity in the project
        :return: Dictionary with blade costs in $/ton
        """
        converted_costs = {}
        for key, value in bt_costs.items():
            converted_value = value / conversion_factor
            converted_costs[key] = converted_value
        return converted_costs

    def update_agent_and_model_variables(self):
        """
        Update instance (agent) and model variables
        """
        self.lifetime_extension_years = \
            self.model.symetric_triang_distrib_draw(
                self.model.lifetime_extension_years[0],
                self.model.lifetime_extension_years[1])
        self.model.le_characteristics.append((self.le_feasibility,
                                              self.lifetime_extension_years))
        # List of tuples: v=wpo.unique_id, w=wpo.blade_mass_conv_factor,
        # x=wpo.p_cap, y=wpo.t_state, z=wpo.mass_conv_factor
        self.assigned_wpo = self.model.assign_agents_to_each_other(
            self.model.variables_additional_wpo,
            sum(self.model.developers.values()), self.model.p_install_growth,
            [], True)
        self.wpo_bt_list = []
        self.model.tp_blade_demanded, self.model.dissolution_available, \
            self.model.blade_type_capacities, self.wpo_bt_list, \
            self.model.total_bt_costs = self.assign_wpo_blade_type(
                self.assigned_wpo, self.bt_costs, self.model.tp_blade_demanded,
                self.model.tp_blade_manufactured,
                self.model.dissolution_available,
                self.model.blade_type_capacities, self.wpo_bt_list,
                self.model.total_bt_costs)
        if self.wpo_bt_list:
            self.blade_type = self.model.most_common_element_list(
                self.wpo_bt_list)

    def step(self):
        """
        Evolution of agent at each step. As Mesa is not built for having
        multiple scheduler, step needs to pass the global scheduler.
        """
        if self.internal_clock == self.model.clock:
            self.install_additional_cap()
            self.update_agent_and_model_variables()
            self.internal_clock += 1
        else:
            pass
