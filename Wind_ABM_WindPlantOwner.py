# -*- coding:utf-8 -*-
"""
Created on December 31 2020

@author Julien Walzberg - Julien.Walzberg@nrel.gov

WindPlantOwner - Circular Economy Wind Agent-based Model (CEWAM)
This module contains the WindPlantOwner class. Wind plant owners make several
decisions, for instance, regarding EOL management.
"""


from mesa import Agent
import random


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
        self.initial_agents = self.model.first_wpo_id + \
            self.model.uswtdb.shape[0]
        # Initial agents:
        if self.unique_id < self.initial_agents:
            self.p_cap = self.model.uswtdb.loc[
                self.unique_id - self.model.first_wpo_id]['p_cap']
            self.p_name = self.model.uswtdb.loc[
                self.unique_id - self.model.first_wpo_id]['p_name']
            self.p_year = self.model.uswtdb.loc[
                self.unique_id - self.model.first_wpo_id]['p_year']
            self.p_tnum = self.model.uswtdb.loc[
                self.unique_id - self.model.first_wpo_id]['p_tnum']
            self.t_state = self.model.uswtdb.loc[
                self.unique_id - self.model.first_wpo_id]['t_state']
            self.t_rd = self.model.uswtdb.loc[
                self.unique_id - self.model.first_wpo_id]['t_rd']
            self.t_cap = self.model.uswtdb.loc[
                self.unique_id - self.model.first_wpo_id]['t_cap']
            self.internal_clock = self.model.clock
            self.eol_pathway = self.model.list_init_eol_pathways.pop()
        # Additional agents:
        else:
            self.t_state = self.model.list_agent_states.pop()
            self.p_cap = \
                self.model.additional_cap[self.t_state] / \
                self.model.dict_agent_states[self.t_state]
            self.p_name = "".join(("Additional_agent_", self.t_state, "_",
                                  str(self.unique_id)))
            self.p_year = self.model.clock + \
                self.model.temporal_scope['simulation_start']
            self.p_tnum = self.p_cap / \
                self.model.uswtdb.groupby('t_state').mean().loc[
                    self.t_state]['t_cap']
            self.t_cap = self.p_cap / self.p_tnum
            self.t_rd = self.model.uswtdb.groupby('t_state').mean().loc[
                               self.t_state]['t_rd']
            self.eol_pathway = self.model.list_add_agent_eol_path.pop()
            self.eol_second_choice = 'landfill'
            self.internal_clock = self.model.clock + 1
        # All agents
        self.mass_conv_factor = self.compute_mass_conv_factor(
            self.t_rd, self.model.blade_size_to_mass_model['coefficient'],
            self.model.blade_size_to_mass_model['power'],
            self.model.blades_per_rotor, self.t_cap)
        self.blade_mass_conv_factor = self.conversion_blade_to_ton(
            self.mass_conv_factor, self.t_cap, self.model.blades_per_rotor)
        self.p_cap_waste = self.p_cap
        self.waste = 0
        self.cum_waste = 0
        self.agent_attributes_counted = False
        self.agent_attributes_updated = False
        self.eol_att_level_ce_path = self.model.trunc_normal_distrib_draw(
            (self.model.attitude_parameters['min'] -
             self.model.attitude_parameters['mean']) /
            self.model.attitude_parameters['standard_deviation'],
            (self.model.attitude_parameters['max'] -
             self.model.attitude_parameters['mean']) /
            self.model.attitude_parameters['standard_deviation'],
            self.model.attitude_parameters['mean'],
            self.model.attitude_parameters['standard_deviation'])
        self.eol_att_level_conv_path = self.model.trunc_normal_distrib_draw(
            (self.model.attitude_parameters['min'] -
             self.model.attitude_parameters['mean']) /
            self.model.attitude_parameters['standard_deviation'],
            (self.model.attitude_parameters['max'] -
             self.model.attitude_parameters['mean']) /
            self.model.attitude_parameters['standard_deviation'],
            (self.model.attitude_parameters['max'] -
             self.model.attitude_parameters['mean']),
            self.model.attitude_parameters['standard_deviation'])
        self.waste_eol_path = self.model.initial_dic_from_key_list(
            self.model.eol_pathways, 0)
        self.variables_developers_wpo = self.convert_developer_costs(
            self.model.variables_developers, self.blade_mass_conv_factor)
        self.eol_pathways_barriers = self.model.initial_dic_from_key_list(
            self.model.eol_pathways.keys(), 0)
        self.eol_tr_cost_shreds, self.eol_tr_cost_segments, \
            self.eol_tr_cost_repair = self.eol_transportation_costs(
              self.eol_distances(self.model.variables_recyclers,
                                 self.model.variables_landfills,
                                 self.model.all_shortest_paths_or_trg))
        self.decommissioning_cost = self.model.symetric_triang_distrib_draw(
            self.model.decommissioning_cost[0],
            self.model.decommissioning_cost[1]) / self.blade_mass_conv_factor
        self.eol_pathways_costs = {}
        self.average_lifetime = self.model.average_lifetime
        self.eol_second_choice = random.choice(self.model.filter_list(
            self.model.list_init_eol_second_choice, self.eol_pathway))
        self.eol_second_choice_share = 0
        self.wpo_eol_pathways = self.model.eol_pathways
        self.le_characteristics = random.choice(self.model.le_characteristics)

    @staticmethod
    def compute_mass_conv_factor(rotor_diameter, coefficient, power,
                                 blades_per_rotor, t_cap):
        """
        Compute a conversion factor to convert EOL volumes from MW to metric
        tons
        :param rotor_diameter: average rotor diameter in meters
        :param coefficient: coefficient of the power function
        :param power: power of the power function
        :param blades_per_rotor: number of blades in wind turbines' rotors
        :param t_cap: average turbine capacity
        :return: conversion factor in metric tons/MW
        """
        blade_radius = rotor_diameter / 2
        mass_blade = coefficient * blade_radius**power
        mass = mass_blade * blades_per_rotor
        conversion_factor = mass / t_cap
        return conversion_factor

    # TODO: specify in doc string that value to convert must be in x/blade
    @staticmethod
    def conversion_blade_to_ton(mass_conv_factor, t_cap, blades_per_rotor):
        conversion_factor = mass_conv_factor * t_cap / blades_per_rotor
        return conversion_factor

    @staticmethod
    def convert_developer_costs(developer_costs, conversion_factor):
        converted_developer_costs = {}
        for key in developer_costs.keys():
            dev_costs_list = developer_costs[key]
            converted_list = [(x, y, z / conversion_factor) for x, y, z in
                              dev_costs_list]
            converted_developer_costs[key] = converted_list
        return converted_developer_costs

    def eol_distances(self, possible_destinations_rec,
                      possible_destinations_land, all_possible_distances):
        distances = {}
        possible_destinations = possible_destinations_rec
        origin = self.t_state
        for key in possible_destinations_land.keys():
            possible_destinations[key] = possible_destinations_land[key]
        for key in possible_destinations.keys():
            list_destinations = possible_destinations[key]
            # in the tuple: x is agent id, y is agent state and z is agent
            # process net cost
            list_distances = [(x, all_possible_distances[origin][y], z) for
                              x, y, z in list_destinations]
            distances[key] = list_distances
            min_distance = min(list_distances, key=lambda t: t[1])[1]
            self.eol_pathways_barriers[key] = min_distance
        return distances

    def transport_shred_costs(self, data, distances):
        shredding_costs = data['shredding_costs']
        shredding_costs = self.model.symetric_triang_distrib_draw(
                shredding_costs[0], shredding_costs[1])
        transport_cost_shreds = data['transport_cost_shreds']
        transport_cost_shreds = self.model.symetric_triang_distrib_draw(
                    transport_cost_shreds[0], transport_cost_shreds[1])
        # in the tuple: x is agent id, y is the distance to agent and z is
        # agent process net cost
        cost_shreds = [(x, shredding_costs + transport_cost_shreds * y) for
                       x, y, z in distances]
        # cost_shreds = min(cost_shreds, key=lambda t: t[1])
        return cost_shreds

    def transport_segment_costs(self, data, distances):
        cutting_costs = data['cutting_costs']
        transport_cost_segments = data['transport_cost_segments']
        # converting $/truck_load-km in $/m_blade-km
        transport_cost_meter = transport_cost_segments / (
                data['length_segment'] * data['segment_per_truck'])
        mass_to_meter = self.mass_conv_factor * self.t_cap / (
                self.t_rd / 2) * self.model.blades_per_rotor
        transport_cost_segments = transport_cost_meter / mass_to_meter
        # in the tuple: x is agent id, y is the distance to agent and z is
        # agent process net cost
        cost_segments = [(x, cutting_costs + transport_cost_segments * y)
                         for x, y, z in distances]
        # cost_segments = min(cost_segments, key=lambda t: t[1])
        return cost_segments

    def eol_transportation_costs(self, distances):
        eol_tr_costs_shreds = {}
        eol_tr_costs_segments = {}
        eol_tr_costs_repair = {}
        for key in self.model.eol_pathways.keys():
            if key in distances:
                eol_tr_costs_shreds[key] = self.transport_shred_costs(
                    self.model.transport_shreds, distances[key])
                eol_tr_costs_segments[key] = self.transport_segment_costs(
                    self.model.transport_segments, distances[key])
            else:
                eol_tr_costs_repair[key] = [
                    (x, y) for x, y, z in self.variables_developers_wpo[key]]
        return eol_tr_costs_shreds, eol_tr_costs_segments, eol_tr_costs_repair

    def costs_eol_pathways(self, eol_tr_costs_shreds, eol_tr_costs_segments,
                           eol_tr_costs_repair, variables_recyclers,
                           variables_landfills, variables_developers,
                           decommissioning_cost):
        costs_eol_pathways = {}
        process_costs = {}
        process_costs.update(variables_landfills)
        process_costs.update(variables_recyclers)
        process_costs.update(variables_developers)
        for key in self.model.eol_pathways.keys():
            transport_mode = self.model.eol_pathways_transport_mode[key]
            if transport_mode == "transport_shreds":
                transport_cost = eol_tr_costs_shreds[key]
                process_costs_key = process_costs[key]
                tr_proc_costs = self.minimum_tr_proc_costs(
                    process_costs_key, transport_cost)
            elif transport_mode == "transport_segments":
                transport_cost = eol_tr_costs_segments[key]
                process_costs_key = process_costs[key]
                tr_proc_costs = self.minimum_tr_proc_costs(
                    process_costs_key, transport_cost)
            elif transport_mode == "transport_repair":
                transport_cost = eol_tr_costs_repair[key]
                process_costs_key = process_costs[key]
                tr_proc_costs = self.minimum_tr_proc_costs(
                    process_costs_key, transport_cost)
            else:
                process_costs_key = process_costs[key]
                transport_cost_shreds = eol_tr_costs_shreds[key]
                tr_proc_costs_shreds = self.minimum_tr_proc_costs(
                    process_costs_key, transport_cost_shreds)
                transport_cost_segments = eol_tr_costs_segments[key]
                tr_proc_costs_segments = self.minimum_tr_proc_costs(
                    process_costs_key, transport_cost_segments)
                tr_proc_costs = min(
                    [tr_proc_costs_shreds + tr_proc_costs_segments],
                    key=lambda t: t[1])
            # in the tuple (x, y): x = agent id, y = transport + process net
            # costs
            costs_eol_pathways[key] = tr_proc_costs[1] + decommissioning_cost
        return costs_eol_pathways

    @staticmethod
    def minimum_tr_proc_costs(process_costs, transport_cost):
        list_process_cost = [(x, z) for x, y, z in process_costs]
        list_all_cost = transport_cost + list_process_cost
        dic_cost = {x: 0 for x, y in list_all_cost}
        for x, y in list_all_cost:
            dic_cost[x] += y
        list_tot_cost = list(map(tuple, dic_cost.items()))
        minimum_tr_proc_cost = min(list_tot_cost, key=lambda t: t[1])
        return minimum_tr_proc_cost

    def update_agent_variables_every_or_specific_step(self):
        """
        Update instance (agent) variables
        """
        # Agents' attributes that should be updated every step
        self.average_lifetime, self.eol_second_choice_share = \
            self.model.lifetime_extension(
                self.eol_pathway, self.model.average_lifetime,
                self.le_characteristics)
        self.waste = self.model.waste_generation(
            self.model.temporal_scope['simulation_start'], self.model.clock,
            self.p_year, self.p_cap_waste, self.average_lifetime,
            self.model.weibull_shape_factor) + self.eol_second_choice_share * \
            self.model.waste_generation(
            self.model.temporal_scope['simulation_start'],
            self.model.clock, self.p_year, self.p_cap_waste,
            self.model.average_lifetime,
            self.model.weibull_shape_factor)
        self.p_cap_waste -= self.waste
        self.cum_waste += self.waste
        self.eol_pathways_costs = self.costs_eol_pathways(
            self.eol_tr_cost_shreds, self.eol_tr_cost_segments,
            self.eol_tr_cost_repair, self.model.variables_recyclers,
            self.model.variables_landfills, self.variables_developers_wpo,
            self.decommissioning_cost)
        self.wpo_eol_pathways = self.model.boolean_dic_based_on_dicts(
            self.wpo_eol_pathways, True, False,
            self.model.bans_enacted[self.t_state])
        # Agents' attributes that should not be updated every step
        if not self.agent_attributes_updated:
            self.eol_pathway, self.eol_second_choice = \
                self.model.theory_planned_behavior_model(
                    self.model.tpb_eol_coeff, self.eol_att_level_ce_path,
                    self.eol_att_level_conv_path, self.wpo_eol_pathways,
                    self.model.choices_circularity, self.model.grid_wpo,
                    'eol_pathway', self.pos, self.eol_pathways_costs,
                    self.eol_pathways_barriers, self.t_state,
                    self.model.regulations_enacted)
            if self.model.early_failure_share * self.p_cap < self.cum_waste:
                self.agent_attributes_updated = True

    def report_agent_variable_once_or_every_step(self):
        """
        Report the value of agent variables across all agents, once or every
        step of the simulation.
        """
        # Agents' attributes that should be counted once
        if not self.agent_attributes_counted:
            self.model.all_cap += self.p_cap
            self.model.states_cap[self.t_state] += self.p_cap
            self.agent_attributes_counted = True
        # Agents' attributes that should be counted every step
        self.model.states_waste[self.t_state] += self.waste * \
            self.mass_conv_factor
        self.model.all_waste += self.waste * self.mass_conv_factor
        self.model.number_wpo_agent += 1
        self.model.eol_pathway_dist_list.append(self.eol_pathway)
        self.model.states_waste_eol_path[self.t_state][self.eol_pathway] += \
            self.waste * self.mass_conv_factor * (
                    1 - self.eol_second_choice_share)
        self.model.states_waste_eol_path[self.t_state][
            self.eol_second_choice] += self.waste * self.mass_conv_factor * \
            self.eol_second_choice_share

    def remove_agent(self):
        """
        Remove an agent once its (the wind turbine project) capacity is close
        to zero
        """
        if self.p_cap_waste < 1E-6:
            self.model.grid_wpo.G.nodes[self.pos]["agent"].remove(self)
            self.model.schedule_wpo.remove(self)
            self.model.schedule.remove(self)

    def step(self):
        """
        Evolution of agent at each step. As Mesa is not built for having
        multiple scheduler, step needs to pass the global scheduler.
        """
        if self.internal_clock == self.model.clock:
            self.update_agent_variables_every_or_specific_step()
            self.report_agent_variable_once_or_every_step()
            self.remove_agent()
            self.internal_clock += 1
        else:
            pass
