# -*- coding:utf-8 -*-
"""
Created on January 11 2021

@author Julien Walzberg - Julien.Walzberg@nrel.gov

Landfill - Circular Economy Wind Agent-based Model (CEWAM)
This module contains the Landfill class. Landfills make several
decisions, for instance, to accept Wind Blades or not.
"""

from mesa import Agent


class Landfill(Agent):
    def __init__(self, unique_id, model, **kwargs):
        super().__init__(unique_id, model)
        """
        Creation of new agent
        """
        for key, value in kwargs.items():
            setattr(self, key, value)
        # Variables internal to the class -
        self.internal_clock = self.model.clock
        self.landfill_type = self.model.wbj_database.loc[
            self.unique_id - self.model.first_land_id]['landfill_type']
        self.landfill_state = self.model.wbj_database.loc[
            self.unique_id - self.model.first_land_id]['State']
        self.landfill_cost = self.model.wbj_database.loc[
            self.unique_id - self.model.first_land_id]['$/ Ton']
        self.remaining_capacity = self.model.wbj_database.loc[
            self.unique_id - self.model.first_land_id][
            'Remaining Capacity (tons)']
        self.close_date = self.model.wbj_database.loc[
            self.unique_id - self.model.first_land_id]['Close Date']
        self.init_remaining_capacity = self.remaining_capacity
        self.yearly_waste = self.model.wbj_database.loc[
            self.unique_id - self.model.first_land_id]['yearly_waste']
        self.landfill_revenue = 0
        self.model.variables_landfills[self.landfill_type].append(
            (self.unique_id, self.landfill_state, self.landfill_cost -
             self.landfill_revenue, self.landfill_cost, self.landfill_revenue))
        self.closure = False
        self.closure_threshold = self.model.symetric_triang_distrib_draw(
            self.model.landfill_closure_threshold[0],
            self.model.landfill_closure_threshold[1])
        self.model.waste_rec_land[self.unique_id] = 0
        self.model.rec_land_volume[self.unique_id] = 0

    @staticmethod
    def closure_update(other_regulations, landfill_state, remaining_capacity,
                       closure_threshold, init_remaining_capacity,
                       simulation_start, clock, close_date):
        year = clock + simulation_start
        if other_regulations[landfill_state]['landfill'] or \
                remaining_capacity < (1 - closure_threshold) * \
                init_remaining_capacity or year > close_date:
            closure = True
        else:
            closure = False
        return closure

    def update_agent_variables(self):
        """
        Update instance (agent) variables
        """
        self.closure = self.closure_update(
            self.model.other_regulations_enacted, self.landfill_state,
            self.remaining_capacity, self.closure_threshold,
            self.init_remaining_capacity,
            self.model.temporal_scope['simulation_start'], self.model.clock,
            self.close_date)
        self.remaining_capacity -= (self.yearly_waste +
                                    self.model.waste_rec_land[self.unique_id])

    # TODO:
    #  * Continue landfill
    #  * mass to volume --> need to be used in landfills
    #  * cost conversion (directly in landfill database) then need to be
    #  accounted in wpo decisions (in costs_eol function in model)

    def report_agent_variables(self):
        """
        Report instance (agent) variables
        """
        if not self.closure:
            self.model.variables_landfills[self.landfill_type].append(
                (self.unique_id, self.landfill_state, self.landfill_cost -
                 self.landfill_revenue, self.landfill_cost,
                 self.landfill_revenue))

    def remove_agent(self):
        """
        Remove the agent if landfill has closed
        """
        if self.closure:
            self.model.grid_land.G.nodes[self.pos]["agent"].remove(self)
            self.model.schedule_land.remove(self)
            self.model.schedule.remove(self)

    def step(self):
        """
        Evolution of agent at each step. As Mesa is not built for having
        multiple scheduler, step needs to pass the global scheduler.
        """
        if self.internal_clock == self.model.clock:
            self.update_agent_variables()
            self.report_agent_variables()
            self.remove_agent()
            self.internal_clock += 1
        else:
            pass
