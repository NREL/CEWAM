# -*- coding:utf-8 -*-
"""
Created on December 31 2020

@author Julien Walzberg - Julien.Walzberg@nrel.gov

WindPlantOwner - Circular Economy Wind Agent-based Model (CEWAM)
This module contains the WindPlantOwner class. Wind plant owners make several
decisions, for instance, regarding EOL management.
"""

# Notes:
# Need to add adoption methods

# TODO:
#  1) Continue building Theory of Planned Behavior model (PICK UP HERE):
#    ii) continue eol costs: decommissioning and processing costs
#  4) Build consequences of lifetime extension: average lifetime is extended

from mesa import Agent


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
        self.growth_rate = self.model.growth_rates.get(self.t_state)
        self.p_cap_waste = self.p_cap
        self.waste = 0
        self.cum_waste = 0
        self.agent_attributes_counted = False
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
        # TODO:
        #  1) replace mock up values below by the computed distances, use mock
        #  up data in recyclers and landfills module (state name) to be able
        #  to develop and test the function (choose closest facility for each
        #  eol pathway)
        self.eol_tr_cost = self.eol_transportation_costs(
            self.eol_distances(self.model.recycler_states,
                               self.model.landfill_states,
                               self.model.all_shortest_paths_or_trg))

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

    def eol_distances(self, possible_destinations_rec,
                      possible_destinations_land, all_possible_distances):
        distances = {}
        possible_destinations = possible_destinations_rec
        origin = self.t_state
        for key in possible_destinations_land.keys():
            possible_destinations[key] = possible_destinations_land[key]
        for key in possible_destinations.keys():
            list_destinations = possible_destinations[key]
            list_distances = []
            for i in range(len(list_destinations)):
                destination = list_destinations[i]
                distance = all_possible_distances[origin][destination]
                list_distances.append(distance)
            distances[key] = min(list_distances)
        return distances

    def transport_shred_costs(self, data, distance):
        shredding_costs = data['shredding_costs']
        shredding_costs = self.model.symetric_triang_distrib_draw(
                shredding_costs[0], shredding_costs[1])
        transport_cost_shreds = data['transport_cost_shreds']
        transport_cost_shreds = self.model.symetric_triang_distrib_draw(
                    transport_cost_shreds[0], transport_cost_shreds[1])
        cost_shreds = shredding_costs + transport_cost_shreds * distance
        return cost_shreds

    def transport_segment_costs(self, data, distance):
        cutting_costs = data['cutting_costs']
        transport_cost_segments = data['transport_cost_segments']
        # converting $/truck_load-km in $/m_blade-km
        transport_cost_meter = transport_cost_segments / (
                data['length_segment'] * data['segment_per_truck'])
        mass_to_meter = self.mass_conv_factor * self.t_cap / (
                self.t_rd / 2) * self.model.blades_per_rotor
        transport_cost_segments = transport_cost_meter / mass_to_meter
        cost_segments = cutting_costs + transport_cost_segments * distance
        return cost_segments

    def eol_transportation_costs(self, distance):
        eol_transport_costs = {}
        for key in self.model.eol_pathways.keys():
            transport_mode = self.model.eol_pathways_transport_mode[key]
            data = getattr(self.model, transport_mode, False)
            if data:
                if transport_mode == 'transport_shreds':
                    eol_transport_costs[key] = self.transport_shred_costs(
                        data, distance[key])
                elif transport_mode == 'transport_segments':
                    eol_transport_costs[key] = self.transport_segment_costs(
                        data, distance[key])
                else:
                    eol_transport_costs[key] = self.model.transport_repair
            else:
                cost_shreds = self.transport_shred_costs(
                    self.model.transport_shreds, distance[key])
                cost_segments = self.transport_segment_costs(
                    self.model.transport_segments, distance[key])
                eol_transport_costs[key] = min(cost_shreds, cost_segments)
        return eol_transport_costs

    def update_agent_variables(self):
        """
        Update instance (agent) variables
        """
        self.waste = self.model.waste_generation(
            self.model.temporal_scope['simulation_start'], self.model.clock,
            self.p_year, self.p_cap_waste, self.model.average_lifetime,
            self.model.weibull_shape_factor)
        self.p_cap_waste -= self.waste
        self.cum_waste += self.waste

    def sum_agent_variable_once_or_every_step(self):
        """
        Sum the value of agent variables across all agents, once or every step
        of the simulation.
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
        self.eol_pathway = self.model.theory_planned_behavior_model(
            self.eol_att_level_ce_path, self.eol_att_level_conv_path,
            self.model.eol_pathways, self.model.choices_circularity,
            'eol_pathway', self.pos)
        self.model.states_waste_eol_path[self.t_state][self.eol_pathway] += \
            self.waste * self.mass_conv_factor

    def remove_agent(self):
        """
        Remove an agent once its (the wind turbine project) capacity is close
        to zero
        """
        if self.p_cap_waste < 1E-6:
            # self.model.grid_wpo.G.nodes[self.unique_id]["agent"].remove(self)
            self.model.grid_wpo.G.nodes[self.pos]["agent"].remove(self)
            self.model.schedule_wpo.remove(self)
            self.model.schedule.remove(self)

    def step(self):
        """
        Evolution of agent at each step. As Mesa is not built for having
        multiple scheduler, step needs to pass the global scheduler.
        """
        if self.internal_clock == self.model.clock:
            self.update_agent_variables()
            self.sum_agent_variable_once_or_every_step()
            self.remove_agent()
            self.internal_clock += 1
        else:
            pass
