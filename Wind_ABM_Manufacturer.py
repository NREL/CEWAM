# -*- coding:utf-8 -*-
"""
Created on December 31 2020

@author Julien Walzberg - Julien.Walzberg@nrel.gov

Manufacturer - Circular Economy Wind Agent-based Model (CEWAM)
This module contains the Manufacturer class. Manufacturers make several
decisions, for instance, regarding the design of wind blades.
"""

from mesa import Agent
import random


class Manufacturer(Agent):
    def __init__(self, unique_id, model, **kwargs):
        super().__init__(unique_id, model)
        """
        Creation of new agent
        """
        for key, value in kwargs.items():
            setattr(self, key, value)
        # Variables internal to the class -
        self.internal_clock = 0
        self.manufacturer_type = self.model.list_manufacturer_types.pop()
        self.state_man = self.model.random_pick_dic_key(
            self.model.growth_rates)
        # Original equipment manufacturer only (wind_blade manufacturer type)
        if self.manufacturer_type == 'wind_blade':
            self.bt_costs = self.model.initial_dic_from_key_list(
                self.model.blade_types.keys(), 0)
            self.bt_costs['thermoset'] = \
                self.model.symetric_triang_distrib_draw(
                    self.model.blade_costs["thermoset"][0],
                    self.model.blade_costs["thermoset"][1])
            self.bt_costs['thermoplastic'] = self.model.blade_costs[
                "thermoplastic_rate"] * self.bt_costs['thermoset']
            self.blade_type = self.model.list_bt_man.pop()
            self.bt_second_choice = random.choice(self.model.filter_list(
                self.model.list_init_bt_second_choice, self.blade_type))
            self.model.variables_manufacturers[self.manufacturer_type].append(
                (self.unique_id, self.bt_costs['thermoset'],
                 self.bt_costs['thermoplastic']))
            self.bt_att_level_ce = self.model.trunc_normal_distrib_draw(
                (self.model.attitude_bt_man_parameters['min'] -
                 self.model.attitude_bt_man_parameters['mean']) /
                self.model.attitude_bt_man_parameters['standard_deviation'],
                (self.model.attitude_bt_man_parameters['max'] -
                 self.model.attitude_bt_man_parameters['mean']) /
                self.model.attitude_bt_man_parameters['standard_deviation'],
                self.model.attitude_bt_man_parameters['mean'],
                self.model.attitude_bt_man_parameters['standard_deviation'])
            self.bt_att_level_conv = self.model.trunc_normal_distrib_draw(
                (self.model.attitude_bt_man_parameters['min'] -
                 (self.model.attitude_bt_man_parameters['max'] -
                  self.model.attitude_bt_man_parameters['mean'])) /
                self.model.attitude_bt_man_parameters['standard_deviation'],
                (self.model.attitude_bt_man_parameters['max'] -
                 (self.model.attitude_bt_man_parameters['max'] -
                  self.model.attitude_bt_man_parameters['mean'])) /
                self.model.attitude_bt_man_parameters['standard_deviation'],
                (self.model.attitude_bt_man_parameters['max'] -
                 self.model.attitude_bt_man_parameters['mean']),
                self.model.attitude_bt_man_parameters['standard_deviation'])
            self.man_blade_types = self.model.blade_types.copy()
            self.bt_barriers = self.model.initial_dic_from_key_list(
                self.model.blade_types.keys(), 0)
            self.development_years = []
            self.development_tp_blade = False
            self.bt_produced = self.model.initial_dic_from_key_list(
                self.model.blade_types.keys(), 0)
            self.market_share = self.model.man_market_share[
                self.manufacturer_type].pop()

    def new_blade_design_adoption(self, current_blade_type):
        """

        :param current_blade_type:
        :return:
        """
        if current_blade_type != 'thermoplastic':
            blade_type = self.model.theory_planned_behavior_model(
                self.model.tpb_bt_man_coeff, self.bt_att_level_ce,
                self.bt_att_level_conv, self.man_blade_types,
                self.model.choices_circularity, self.model.grid_oem,
                'blade_type', self.pos, self.bt_costs, self.bt_barriers,
                self.state_man, self.model.regulations_enacted)[0]
        else:
            blade_type = current_blade_type
        return blade_type

    @staticmethod
    def lag_time_redesign(development_years, lag_time_tp_blade_dev):
        """
        Define the period of time during which the new blade design
        (thermoplastic blade) is being developed
        :param development_years: list representing the number of years that
        the thermoplastic blade design has been adopted
        :param lag_time_tp_blade_dev: the required period between the first
        decision (adoption) of the thermoplastic design and the effective sales
        of thermoplastic blades
        :return: a Boolean used to set up production of thermoplastic blade
        """
        last_dev_years = development_years[-lag_time_tp_blade_dev:]
        tp_dev_years = last_dev_years.count('thermoplastic')
        if tp_dev_years == lag_time_tp_blade_dev:
            development_decision = True
        else:
            development_decision = False
        return development_decision

    @staticmethod
    def quantity_tp_blade_produced(development_tp_blade, bt_produced,
                                   producer_market_share, tp_production_share,
                                   additional_capacity):
        """
        Compute the quantity of thermoplastic blades produced
        :param development_tp_blade: a Boolean signifying that the manufacturer
        has now the capability to produce thermoplastic blades
        :param bt_produced: the amount of blade produced for each type
        :param producer_market_share: market share of the manufacturer
        :param tp_production_share: share of the production line allocated to
        thermoplastic blade manufacturing
        :param additional_capacity: amount of new blades to be produced at the
        current time step of the simulation
        :return: the amount of blade produced for each type
        """
        if development_tp_blade:
            tp_share = tp_production_share
        else:
            tp_share = 0
        total_capacity_installed = sum(additional_capacity.values())
        bt_produced['thermoplastic'] = tp_share * producer_market_share * \
            total_capacity_installed
        bt_produced['thermoset'] = (1 - tp_share) * producer_market_share * \
            total_capacity_installed
        return bt_produced

    @staticmethod
    def manufacturing_waste(additional_capacity, producer_market_share,
                            wgt_avr_mass_c_fact, manufacturing_waste_ratio,
                            material_mass_fractions, manufacturing_waste_q):
        """
        Compute manufacturing waste from finished blade mass
        :param additional_capacity: finished blade capacity (MW)
        :param producer_market_share: market share of the manufacturer
        :param wgt_avr_mass_c_fact: weighted average mass conversion factor
        (metric tons/MW)
        :param manufacturing_waste_ratio: ratio of manufacturing waste for each
        material
        :param material_mass_fractions: mass fraction of the different material
        in wind blades
        :param manufacturing_waste_q: quantity of manufacturing waste for each
        materials
        :return: quantity of manufacturing waste for each materials
        """
        total_capacity_installed = sum(additional_capacity.values())
        producer_share = total_capacity_installed * producer_market_share * \
            wgt_avr_mass_c_fact
        for key in manufacturing_waste_q.keys():
            manufacturing_waste_q[key] += material_mass_fractions[key] * \
                                          manufacturing_waste_ratio[key] * \
                                          producer_share
        return manufacturing_waste_q

    def update_agent_variables(self):
        """
        Update instance (agent) variables
        """
        if self.manufacturer_type == 'wind_blade':
            self.blade_type = self.new_blade_design_adoption(self.blade_type)
            self.development_years.append(self.blade_type)
            self.development_tp_blade = self.lag_time_redesign(
                self.development_years, self.model.lag_time_tp_blade_dev)
            self.bt_produced = self.quantity_tp_blade_produced(
                self.development_tp_blade, self.bt_produced,
                self.market_share, self.model.tp_production_share,
                self.model.additional_cap)

    def report_agent_variables(self):
        """
        Report instance (agent) variables
        """
        if self.manufacturer_type == 'wind_blade':
            self.model.tp_blade_manufactured += self.bt_produced[
                'thermoplastic']
            self.model.bt_manufactured_q = \
                self.model.instant_to_cumulative_dic(
                    self.bt_produced, self.model.bt_manufactured_q)
            self.model.manufacturing_waste_q = self.manufacturing_waste(
                self.model.additional_cap, self.market_share,
                self.model.weighted_avr_mass_conv_factor,
                self.model.manufacturing_waste_ratio,
                self.model.blade_mass_fractions,
                self.model.manufacturing_waste_q)

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
