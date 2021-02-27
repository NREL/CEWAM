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
        self.recycler_cost = 0
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
        if (clock + simulation_start) == simulation_start:
            self.init_recycled_quantity = waste_rec_land[unique_id]

    def learning_effect(self, original_volume, volume, original_cost,
                        shape_factor):
        if volume and original_volume > 0:
            decreased_cost = self.learning_function(
                original_volume, volume, original_cost, shape_factor)
            if decreased_cost < original_cost:
                cost = decreased_cost
            else:
                cost = original_cost
        else:
            cost = original_cost
        return cost

    @staticmethod
    def learning_function(original_volume, volume, original_cost,
                          shape_factor):
        decreased_cost = original_cost * \
                         (volume / original_volume)**shape_factor
        return decreased_cost

    @staticmethod
    def material_recovery(recycled_quantity, blade_mass_fractions,
                          rec_recovery_fractions, recycler_type,
                          recovered_materials):
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
            self.init_recycler_cost, self.learning_parameter)

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
