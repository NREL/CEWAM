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
            (self.model.attitude_eol_parameters['min'] -
             self.model.attitude_eol_parameters['mean']) /
            self.model.attitude_eol_parameters['standard_deviation'],
            (self.model.attitude_eol_parameters['max'] -
             self.model.attitude_eol_parameters['mean']) /
            self.model.attitude_eol_parameters['standard_deviation'],
            self.model.attitude_eol_parameters['mean'],
            self.model.attitude_eol_parameters['standard_deviation'])
        self.eol_att_level_conv_path = self.model.trunc_normal_distrib_draw(
            (self.model.attitude_eol_parameters['min'] -
             (self.model.attitude_eol_parameters['max'] -
              self.model.attitude_eol_parameters['mean'])) /
            self.model.attitude_eol_parameters['standard_deviation'],
            (self.model.attitude_eol_parameters['max'] -
             (self.model.attitude_eol_parameters['max'] -
              self.model.attitude_eol_parameters['mean'])) /
            self.model.attitude_eol_parameters['standard_deviation'],
            (self.model.attitude_eol_parameters['max'] -
             self.model.attitude_eol_parameters['mean']),
            self.model.attitude_eol_parameters['standard_deviation'])
        self.waste_eol_path = self.model.initial_dic_from_key_list(
            self.model.eol_pathways.keys(), 0)
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
        self.wpo_eol_pathways = self.model.eol_pathways.copy()
        self.le_characteristics = random.choice(self.model.le_characteristics)
        self.regulation_new_decision = False
        self.eol_unique_ids_selected = self.model.initial_dic_from_key_list(
            self.model.eol_pathways.keys(), 0)
        # Additional agents - variables for other agents
        if self.unique_id > self.initial_agents:
            self.model.variables_additional_wpo.append(
                (self.unique_id, self.blade_mass_conv_factor, self.p_cap,
                 self.t_state, self.mass_conv_factor))

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

    @staticmethod
    def conversion_blade_to_ton(mass_conv_factor, t_cap, blades_per_rotor):
        """
        Calculate a conversion factor in tons/blade
        :param mass_conv_factor: mass conversion factor in tons/MW
        :param t_cap: capacity in MW
        :param blades_per_rotor: number of blades per rotor
        :return: conversion factor in tons/blade
        """
        conversion_factor = mass_conv_factor * t_cap / blades_per_rotor
        return conversion_factor

    @staticmethod
    def convert_developer_costs(developer_costs, conversion_factor):
        """
        Convert developer costs from $/blade to $/tons
        :param developer_costs: dictionary of tuple containing (unique_id,
        repair transportation costs, process costs) of the developer with
        process costs in $/blade
        :param conversion_factor: conversion factors in tons/blade
        :return: original tuple but with process costs in $/tons
        """
        converted_developer_costs = {}
        for key in developer_costs.keys():
            dev_costs_list = developer_costs[key]
            converted_list = [(x, y, z / conversion_factor) for x, y, z in
                              dev_costs_list]
            converted_developer_costs[key] = converted_list
        return converted_developer_costs

    def eol_distances(self, possible_destinations_rec,
                      possible_destinations_land, all_possible_distances):
        """
        Compute the distances to all eol facilities for each eol pathway
        :param possible_destinations_rec: all possible destinations for the
        recycling eol pathways
        :param possible_destinations_land: all possible destinations for the
        landfill eol pathway
        :param all_possible_distances: distances to all possible destinations
        :return: the distances to all eol facilities for each eol pathway
        """
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
        """
        Compute costs when blades are shredded before transportation
        :param data: shredding process and transportation costs
        :param distances: distances from wind farm site (where shredding
        occurs) to the eol facility
        :return: the cost associated with shredding and transporting shreds
        to the eol site
        """
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
        return cost_shreds

    def transport_segment_costs(self, data, distances):
        """
        Compute costs when blades are cut before transportation
        :param data: cutting process and transportation costs
        :param distances: distances from wind farm site (where cutting
        occurs) to the eol facility
        :return: the cost associated with cutting and transporting segments
        to the eol site
        """
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
        return cost_segments

    def eol_transportation_costs(self, distances):
        """
        Compute transportation costs according for all options: shredded
        blades, cut blades or for repair
        :param distances: distances to each eol facility from the Wind farm
        :return: transportation costs for all options
        """
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
        """
        Compute costs for each eol pathway accounting for decommissioning costs
        (similar for each eol pathway), transportation costs (including
        pre-processing (shredding or cutting), and eol net costs (costs minus
        potential revenue)
        :param eol_tr_costs_shreds: transportation after shredding costs
        :param eol_tr_costs_segments: transportation after cutting costs
        :param eol_tr_costs_repair: transportation costs for repair
        :param variables_recyclers: unique_id, location, process cost
        :param variables_landfills: unique_id, location, landfill cost
        :param variables_developers: unique_id, transportation cost, process
        cost
        :param decommissioning_cost: decommissioning cost, similar for all eol
        pathway
        :return: costs for each eol pathway
        """
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
                    [tr_proc_costs_shreds, tr_proc_costs_segments],
                    key=lambda t: t[1])
            # in the tuple (x, y): x = agent id, y = transport + process net
            # costs
            self.eol_unique_ids_selected[key] = tr_proc_costs[0]
            if key == 'lifetime_extension':
                costs_eol_pathways[key] = tr_proc_costs[1]
            else:
                costs_eol_pathways[key] = tr_proc_costs[1] + \
                                          decommissioning_cost
        return costs_eol_pathways

    @staticmethod
    def minimum_tr_proc_costs(process_costs, transport_cost):
        """
        Minimize transportation and process costs when several options (eol
        facilities) ara available in a given eol pathway
        :param process_costs: list of tuple containing unique_id, location, and
        process cost of all facilities providing the given eol service
        :param transport_cost: list of tuple containing unique_id and
        transportation costs of all facilities providing the given eol service
        :return: a tuple containing the unique_id of the facility with the
        lowest sum of transportation and process cost (second element of the
        tuple)
        """
        list_process_cost = [(x, z) for x, y, z in process_costs]
        list_all_cost = transport_cost + list_process_cost
        dic_cost = {x: 0 for x, y in list_all_cost}
        for x, y in list_all_cost:
            dic_cost[x] += y
        list_tot_cost = list(map(tuple, dic_cost.items()))
        minimum_tr_proc_cost = min(list_tot_cost, key=lambda t: t[1])
        return minimum_tr_proc_cost

    @staticmethod
    def report_variables_if_lifetime_extended_or_else(
            eol_pathway, eol_second_choice, eol_unique_ids_selected,
            reporter_waste, reporter_adoption, reporter_recycler, state, waste,
            mass_conv_factor):
        """
        Report waste according to the eol pathway - if lifetime extension is
        adopted, waste is reported to the secondary pathway, otherwise it is
        reported in the primary pathway
        :param eol_pathway: primary pathway adopted by wpo
        :param eol_second_choice: secondary pathway adopted by wpo
        :param eol_unique_ids_selected:
        :param reporter_waste: nested dictionary reporter of waste amount in
        the state of the wpo and the pathway adopted for eol blades
        :param reporter_adoption: dictionary of the number of wpo that have
        adopted each eol pathway
        :param reporter_recycler:
        :param state: the state of the wpo
        :param waste: the waste of the wpo (in MW)
        :param mass_conv_factor: the conversion factor (metric ton / MW)
        """
        if eol_pathway == 'lifetime_extension':
            reporter_waste[state][eol_second_choice] += waste * \
                                                        mass_conv_factor
            reporter_adoption[eol_pathway] += 1
            reporter_adoption[eol_second_choice] += 1
            reporter_recycler[eol_unique_ids_selected[eol_second_choice]] += \
                waste * mass_conv_factor
        else:
            reporter_waste[state][eol_pathway] += waste * \
                                                        mass_conv_factor
            reporter_adoption[eol_pathway] += 1
            reporter_recycler[eol_unique_ids_selected[eol_pathway]] += \
                waste * mass_conv_factor

    def other_agents_consequences(self):
        """
        Signal the update_agent_variables_every_or_specific_step function that
        wpo eol pathway need to be updated with regards to new information from
        other agents
        """
        self.wpo_eol_pathways = self.model.boolean_dic_based_on_dicts(
            self.wpo_eol_pathways, True, False,
            self.model.bans_enacted[self.t_state])
        if bool(self.model.dissolution_available) and self.unique_id in \
                self.model.dissolution_available:
            self.wpo_eol_pathways = self.model.boolean_dic_based_on_dicts(
                self.wpo_eol_pathways, True, True,
                self.model.dissolution_available[self.unique_id])
        for value in self.model.regulations_enacted.values():
            if value[self.t_state] and not self.regulation_new_decision:
                self.agent_attributes_updated = False
                self.regulation_new_decision = True

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
        self.other_agents_consequences()
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
        self.report_variables_if_lifetime_extended_or_else(
            self.eol_pathway, self.eol_second_choice,
            self.eol_unique_ids_selected, self.model.states_waste_eol_path,
            self.model.eol_pathway_adoption, self.model.waste_rec_land,
            self.t_state, self.waste, self.mass_conv_factor)

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
