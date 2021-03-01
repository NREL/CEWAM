# -*- coding:utf-8 -*-
"""
Created on January 11 2021

@author Julien Walzberg - Julien.Walzberg@nrel.gov

Recycler - Circular Economy Wind Agent-based Model (CEWAM)
This module contains the Recycler class. Recyclers make several
decisions, for instance, what type of recycling to perform.
"""


from mesa import Agent


class Recycler(Agent):
    def __init__(self, unique_id, model, **kwargs):
        super().__init__(unique_id, model)
        """
        Creation of new agent
        """
        for key, value in kwargs.items():
            setattr(self, key, value)
        # Variables internal to the class -
        self.internal_clock = 0
        self.recycler_type = self.model.list_recycler_types.pop()
        self.recycler_state = self.model.assign_elements_from_list(
            self.model.recyclers_states[self.recycler_type], True)
        self.init_recycler_cost = self.model.symetric_triang_distrib_draw(
            self.model.rec_processes_costs[self.recycler_type][0],
            self.model.rec_processes_costs[self.recycler_type][1])
        self.recycler_revenue = self.model.symetric_triang_distrib_draw(
            self.model.rec_processes_revenues[self.recycler_type][0],
            self.model.rec_processes_revenues[self.recycler_type][1])
        self.model.variables_recyclers[self.recycler_type].append(
            (self.unique_id, self.recycler_state, (self.init_recycler_cost -
                                                   self.recycler_revenue)))
        self.recycler_cost = self.init_recycler_cost
        self.init_recycled_quantity = 0
        self.recycled_quantity = 0
        self.model.waste_rec_land[self.unique_id] = 0
        self.learning_parameter = self.model.symetric_triang_distrib_draw(
            self.model.learning_parameter[self.recycler_type][0],
            self.model.learning_parameter[self.recycler_type][1])
        self.model.average_recycler_costs[self.recycler_type] += \
            self.init_recycler_cost / self.model.recyclers[self.recycler_type]

    def initial_recycling_quantity(self, clock, unique_id, simulation_start,
                                   waste_rec_land):
        """
        Compute the initial recycled quantity (at year 0 of the simulation)
        :param clock: the time step of the simulation
        :param unique_id: the recycler agent's unique id
        :param simulation_start: the year the simulation start
        :param waste_rec_land: waste that is either recycled or landfilled
        """
        if (clock + simulation_start) == simulation_start:
            self.init_recycled_quantity = waste_rec_land[unique_id]

    def learning_effect(self, original_volume, volume, original_cost,
                        current_cost, learning_parameter):
        """
        Model the learning effect from recycler: as the quantity of blades
        sent to recyclers increases, the recyclers can lower their processes'
        costs, e.g., due to economies of scale and technological advancement;
        cost can only decreased, if recycled quantity decreases, the recycling
        cost remain the same as its current value
        :param original_volume: the original quantity of blades recycled
        (at the beginning of the simulation)
        :param volume: the volume of blade recycled currently (at the current
        time step)
        :param original_cost: the initial recycling cost (at the beginning of
        the simulation)
        :param current_cost: the current recycling cost
        :param learning_parameter: parameter of the learning function used to
        model the learning effect
        :return: the current recycling cost
        """
        if volume and original_volume > 0:
            decreased_cost = self.learning_function(
                original_volume, volume, original_cost, learning_parameter)
            if decreased_cost < original_cost:
                cost = decreased_cost
            else:
                cost = current_cost
        else:
            cost = current_cost
        return cost

    @staticmethod
    def learning_function(original_volume, volume, original_cost,
                          learning_parameter):
        """
        The learning function used to model the learning effect
        :param original_volume: the original quantity of blades recycled
        (at the beginning of the simulation)
        :param volume: the volume of blade recycled currently (at the current
        time step)
        :param original_cost: the initial recycling cost (at the beginning of
        the simulation)
        :param learning_parameter: parameter of the learning function used to
        model the learning effect
        :return: the decreased costs due to the learning effect
        """
        decreased_cost = original_cost * \
            (volume / original_volume)**learning_parameter
        return decreased_cost

    @staticmethod
    def material_recovery(recycled_quantity, blade_mass_fractions,
                          rec_recovery_fractions, recycler_type,
                          recovered_materials):
        """
        Compute the amount or material recovered in the different recycling
        processes of the different recyclers
        :param recycled_quantity: quantity of blade recycled by the recycler
        agent
        :param blade_mass_fractions: material mass fraction of blades
        :param rec_recovery_fractions: recovery fractions of the recycler agent
         recycling process for each materials
        :param recycler_type: type of the recycler agent determining its
        recycling processes and thus material recovery fractions
        :param recovered_materials: dictionary containing the cumulative
        quantities recovered for each materials
        :return: the dictionary recovered_materials
        """
        for key in blade_mass_fractions.keys():
            mat_recovered = recycled_quantity * blade_mass_fractions[key] * \
                            rec_recovery_fractions[recycler_type][key]
            recovered_materials[key] += mat_recovered
        return recovered_materials

    def update_agent_variables(self):
        """
        Update instance (agent) variables
        """
        self.initial_recycling_quantity(
            self.model.clock, self.unique_id,
            self.model.temporal_scope['simulation_start'],
            self.model.waste_rec_land)
        self.recycled_quantity = self.model.waste_rec_land[self.unique_id]
        self.recycler_cost = self.learning_effect(
            self.init_recycled_quantity, self.recycled_quantity,
            self.init_recycler_cost, self.recycler_cost,
            self.learning_parameter)

    def report_agent_variables(self):
        """
        Report instance (agent) variables
        """
        self.model.variables_recyclers[self.recycler_type].append(
            (self.unique_id, self.recycler_state, self.recycler_cost))
        self.model.average_recycler_costs[self.recycler_type] += \
            self.recycler_cost / self.model.recyclers[self.recycler_type]
        self.model.recovered_materials = self.material_recovery(
            self.recycled_quantity, self.model.blade_mass_fractions,
            self.model.rec_recovery_fractions, self.recycler_type,
            self.model.recovered_materials)

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
