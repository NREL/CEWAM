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
import numpy as np
import copy
import math


class Manufacturer(Agent):
    def __init__(self, unique_id, model, **kwargs):
        super().__init__(unique_id, model)
        """
        Creation of new agent
        """
        for key, value in kwargs.items():
            setattr(self, key, value)
        # Variables internal to the class -
        self.internal_clock = self.model.clock
        self.manufacturer_type = self.model.list_manufacturer_types.pop()
        # Original equipment manufacturer only (wind_blade manufacturer type)
        if self.manufacturer_type == 'wind_blade':
            self.state_man = self.model.assign_elements_from_list(
                self.model.oem_states[self.manufacturer_type], True)
            self.bt_costs = self.model.initial_dic_from_key_list(
                self.model.blade_types.keys(), 0)
            self.bt_costs['thermoset'] = \
                self.model.symetric_triang_distrib_draw(
                    self.model.blade_costs["thermoset"][0],
                    self.model.blade_costs["thermoset"][1])
            self.tp_blade_rate = self.model.symetric_triang_distrib_draw(
                self.model.blade_costs["thermoplastic_rate"][0],
                self.model.blade_costs["thermoplastic_rate"][1])
            self.bt_costs['thermoplastic'] = self.tp_blade_rate * \
                self.bt_costs['thermoset']
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
            self.market_share = 1 / self.model.manufacturers['wind_blade']
            self.eol_man_wst_path = self.model.list_man_waste.pop()
            self.man_eol_pathways = {
                key: self.model.eol_pathways[key] for
                key in self.model.man_waste_dist_init.keys()}
            self.man_wst_att_level_ce = self.model.trunc_normal_distrib_draw(
                (self.model.attitude_man_waste_parameters['min'] -
                 self.model.attitude_man_waste_parameters['mean']) /
                self.model.attitude_man_waste_parameters['standard_deviation'],
                (self.model.attitude_man_waste_parameters['max'] -
                 self.model.attitude_man_waste_parameters['mean']) /
                self.model.attitude_man_waste_parameters['standard_deviation'],
                self.model.attitude_man_waste_parameters['mean'],
                self.model.attitude_man_waste_parameters['standard_deviation'])
            self.man_wst_att_level_conv = self.model.trunc_normal_distrib_draw(
                (self.model.attitude_man_waste_parameters['min'] -
                 (self.model.attitude_man_waste_parameters['max'] -
                  self.model.attitude_man_waste_parameters['mean'])) /
                self.model.attitude_man_waste_parameters['standard_deviation'],
                (self.model.attitude_man_waste_parameters['max'] -
                 (self.model.attitude_man_waste_parameters['max'] -
                  self.model.attitude_man_waste_parameters['mean'])) /
                self.model.attitude_man_waste_parameters['standard_deviation'],
                (self.model.attitude_man_waste_parameters['max'] -
                 self.model.attitude_man_waste_parameters['mean']),
                self.model.attitude_man_waste_parameters['standard_deviation'])
            self.man_wst_barriers = self.model.initial_dic_from_key_list(
                self.model.eol_pathways.keys(), 0)
            self.man_wst_costs = self.model.initial_dic_from_key_list(
                self.model.eol_pathways.keys(), 0)
            self.man_wst_transport_costs = self.model.eol_transportation_costs(
                self.model.eol_pathways, self.model.eol_distances(
                    self.model.variables_recyclers,
                    self.model.variables_landfills,
                    self.model.state_distances, self.state_man,
                    self.man_wst_barriers, False),
                self.model.transport_shred_costs, self.model.transport_shreds,
                self.model.transport_segment_costs,
                self.model.transport_segments, self.model.variables_developers,
                self.model.symetric_triang_distrib_draw, np.NaN, np.NaN,
                np.NaN, self.model.blades_per_rotor)
            self.recycling_shreds_onsite(
                self.model.transport_shreds, self.man_wst_transport_costs[0],
                self.model.symetric_triang_distrib_draw)
            self.man_wst_u_ids_selected = self.model.initial_dic_from_key_list(
                self.model.eol_pathways.keys(), 0)
            self.learning_parameters = {}
            self.man_wst_volume = self.model.initial_dic_from_key_list(
                self.man_eol_pathways.keys(), 0)
            self.init_m_wst_rec_cost, self.init_m_wst_rec_rev, \
                self.learning_parameters = \
                self.init_m_wst_rec_cost_learning_model(
                    self.man_eol_pathways,
                    self.model.symetric_triang_distrib_draw,
                    self.model.rec_processes_costs,
                    self.model.rec_processes_revenues,
                    self.model.learning_parameter)
            self.m_wst_rec_cost = copy.deepcopy(self.init_m_wst_rec_cost)
            self.tb_lifetime = self.model.symetric_triang_distrib_draw(
                self.model.average_lifetime['thermoplastic'][0],
                self.model.average_lifetime['thermoplastic'][1])
            self.m_wst_rev = {}
            self.yearly_man_waste = 0
        else:
            self.state_man = self.model.random_pick_dic_key(
                self.model.growth_rates)

    def new_blade_design_adoption(self, current_blade_type):
        if current_blade_type != 'thermoplastic':
            blade_type = self.model.theory_planned_behavior_model(
                self.model.tpb_bt_man_coeff, self.bt_att_level_ce,
                self.bt_att_level_conv, self.man_blade_types,
                self.model.choices_circularity, self.model.grid_oem,
                'blade_type', self.pos, self.bt_costs, self.bt_barriers,
                self.state_man, self.model.regulations_enacted)[0]
        else:
            blade_type = current_blade_type
            self.man_eol_pathways['dissolution'] = True
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

    def manufacturing_waste(self, additional_capacity, producer_market_share,
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
        for key, value in manufacturing_waste_ratio.items():
            waste_ratio_range = value
            waste_ratio = self.model.symetric_triang_distrib_draw(
                waste_ratio_range[0], waste_ratio_range[1])
            man_wst = material_mass_fractions[key] * waste_ratio * \
                producer_share
            manufacturing_waste_q[self.eol_man_wst_path][key] += man_wst
            self.man_wst_volume[self.eol_man_wst_path] += man_wst
        yearly_man_wst = producer_share
        return manufacturing_waste_q, yearly_man_wst

    @staticmethod
    def recycling_shreds_onsite(data, man_wst_transport_costs,
                                symetric_triang_distrib_draw):
        shredding_costs = data['shredding_costs']
        shred_cost = symetric_triang_distrib_draw(shredding_costs[0],
                                                  shredding_costs[1])
        for key, value in man_wst_transport_costs.items():
            if key != "landfill":
                man_wst_transport_costs[key] = \
                    [(x, shred_cost) for x, y in value]

    def costs_man_waste(self):
        # Manufacturing waste is transported to landfills as shreds
        transport_mode = copy.deepcopy(self.model.eol_pathways_transport_mode)
        transport_mode["landfill"] = 'transport_shreds'
        recycling_costs = copy.deepcopy(self.model.variables_recyclers)
        for key in recycling_costs.keys():
            if key in self.man_eol_pathways:
                volume = self.man_wst_volume[key]
                original_volume = self.model.recycling_init_cap[key]
                self.m_wst_rec_cost[key] = self.model.learning_effect(
                    original_volume, volume, self.init_m_wst_rec_cost[key],
                    self.m_wst_rec_cost[key], self.learning_parameters[key],
                    self.model.learning_function)
                recycling_costs[key] = [
                    (self.unique_id, self.state_man, self.m_wst_rec_cost[key] -
                     self.init_m_wst_rec_rev[key], self.m_wst_rec_cost[key],
                     self.init_m_wst_rec_rev[key], np.nan)]
        man_wst_costs, m_wst_rev, unused_variable = \
            self.model.costs_eol_pathways(
                self.man_wst_transport_costs[0],
                self.man_wst_transport_costs[1],
                self.man_wst_transport_costs[2],
                recycling_costs, self.model.variables_landfills,
                self.model.variables_developers, 0, self.model.eol_pathways,
                transport_mode, self.model.minimum_tr_proc_costs,
                self.man_wst_u_ids_selected, self.model.convert_unit_land_cost,
                self.model.waste_volume_model,
                self.model.transport_shreds_mandate, self.state_man)
        return man_wst_costs, m_wst_rev

    @staticmethod
    def init_m_wst_rec_cost_learning_model(
            man_eol_pathways, sym_trig_dist, rec_processes_costs,
            rec_processes_rev, learning_param_model):
        init_rec_cost = {}
        init_rec_rev = {}
        learning_parameters = {}
        for key in man_eol_pathways.keys():
            if key in rec_processes_costs:
                proc_cost = rec_processes_costs[key]
                cost = sym_trig_dist(proc_cost[0], proc_cost[1])
                init_rec_cost[key] = cost
                proc_rev = rec_processes_rev[key]
                rev = sym_trig_dist(proc_rev[0], proc_rev[1])
                init_rec_rev[key] = rev
                learning_params = learning_param_model[key]
                l_param = sym_trig_dist(learning_params[0], learning_params[1])
                learning_parameters[key] = l_param
        return init_rec_cost, init_rec_rev, learning_parameters

    @staticmethod
    def landfill_waste(waste_volume_model, eol_man_wst_path, reporter_rec_land,
                       rec_land_volume, man_wst_u_ids_selected,
                       yearly_man_waste):
        if eol_man_wst_path == 'landfill':
            reporter_rec_land[man_wst_u_ids_selected[eol_man_wst_path]] += \
                yearly_man_waste
            if waste_volume_model['waste_volume']:
                rec_land_volume[man_wst_u_ids_selected[eol_man_wst_path]] += \
                    yearly_man_waste / waste_volume_model['transport_shreds']
        else:
            pass

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
            self.man_wst_costs, self.m_wst_rev = self.costs_man_waste()
            self.eol_man_wst_path = self.model.theory_planned_behavior_model(
                self.model.tpb_man_waste_coeff, self.man_wst_att_level_ce,
                self.man_wst_att_level_conv, self.man_eol_pathways,
                self.model.choices_circularity, self.model.grid_oem,
                'eol_man_wst_path', self.pos, self.man_wst_barriers,
                self.man_wst_costs, self.state_man,
                self.model.regulations_enacted)[0]

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
            self.model.manufacturing_waste_q, self.yearly_man_waste = \
                self.manufacturing_waste(
                    self.model.additional_cap, self.market_share,
                    self.model.weighted_avr_mass_conv_factor,
                    self.model.manufacturing_waste_ratio,
                    self.model.blade_mass_fractions,
                    self.model.manufacturing_waste_q)
            self.model.list_tb_lifetimes.extend(
                [self.tb_lifetime] * int(
                    math.ceil(self.market_share *
                              self.model.manufacturers[
                                  self.manufacturer_type])))
            self.model.total_man_waste_costs[self.eol_man_wst_path] = \
                self.man_wst_volume[self.eol_man_wst_path] * \
                (self.man_wst_costs[self.eol_man_wst_path] +
                 self.m_wst_rev[self.eol_man_wst_path])
            self.model.total_man_waste_revenues[self.eol_man_wst_path] = \
                self.man_wst_volume[self.eol_man_wst_path] * \
                self.m_wst_rev[self.eol_man_wst_path]
            self.landfill_waste(
                self.model.waste_volume_model, self.eol_man_wst_path,
                self.model.waste_rec_land, self.model.rec_land_volume,
                self.man_wst_u_ids_selected, self.yearly_man_waste)

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
