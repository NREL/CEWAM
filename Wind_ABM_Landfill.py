# -*- coding:utf-8 -*-
"""
Created on January 11 2021

@author Julien Walzberg - Julien.Walzberg@nrel.gov

Landfill - Circular Economy Wind Agent-based Model (CEWAM)
This module contains the Landfill class. Landfills make several
decisions, for instance, to accept Wind Blades or not.
"""

from mesa import Agent
import numpy as np


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
        if self.model.detailed_transport_model:
            self.landfill_name = self.model.wbj_database.loc[
                self.unique_id - self.model.first_land_id]['Facility Name']
        else:
            self.landfill_name = self.landfill_state
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
        # only potential costs are seen by wind plant owners, potential
        # revenues are kept by landfills
        self.model.variables_landfills[self.landfill_type].append(
            (self.unique_id, self.landfill_state, max(self.landfill_cost -
             self.landfill_revenue, 0), self.landfill_cost,
             self.landfill_revenue))
        self.model.variables_landfills_tr[self.landfill_type].append(
            (self.unique_id, self.landfill_name, max(self.landfill_cost -
             self.landfill_revenue, 0), self.landfill_cost,
             self.landfill_revenue))
        self.closure = False
        self.closure_threshold = self.model.symetric_triang_distrib_draw(
            self.model.landfill_closure_threshold[0],
            self.model.landfill_closure_threshold[1])
        self.model.waste_rec_land[self.unique_id] = 0
        self.model.rec_land_volume[self.unique_id] = 0
        self.model.init_land_capacity[self.landfill_state] += \
            self.init_remaining_capacity
        self.blade_waste = 0
        self.model.average_eol_costs[self.landfill_type] += \
            self.landfill_cost / self.model.wbj_database.shape[0]

    @staticmethod
    def closure_update(remaining_capacity, closure_threshold,
                       init_remaining_capacity, simulation_start, clock,
                       close_date):
        year = clock + simulation_start
        if remaining_capacity < (1 - closure_threshold) * \
                init_remaining_capacity or year > close_date:
            closure = True
        else:
            closure = False
        return closure

    @staticmethod
    def volume_model(waste_volume_model, yearly_waste, waste_rec_land,
                     rec_land_volume, unique_id, remaining_capacity):
        if waste_volume_model['waste_volume']:
            waste_added_to_landfill = yearly_waste + rec_land_volume[unique_id]
            blade_waste = rec_land_volume[unique_id]
        else:
            waste_added_to_landfill = yearly_waste + waste_rec_land[unique_id]
            blade_waste = waste_rec_land[unique_id]
        remaining_capacity = remaining_capacity - waste_added_to_landfill
        if remaining_capacity > 0:
            return remaining_capacity, blade_waste
        else:
            return 0, blade_waste

    def update_agent_variables(self):
        """
        Update instance (agent) variables
        """
        self.remaining_capacity, self.blade_waste = self.volume_model(
            self.model.waste_volume_model, self.yearly_waste,
            self.model.waste_rec_land, self.model.rec_land_volume,
            self.unique_id, self.remaining_capacity)
        self.closure = self.closure_update(
            self.remaining_capacity, self.closure_threshold,
            self.init_remaining_capacity,
            self.model.temporal_scope['simulation_start'], self.model.clock,
            self.close_date)

    def report_agent_variables(self):
        """
        Report instance (agent) variables
        """
        if not self.closure:
            self.model.variables_landfills[self.landfill_type].append(
                (self.unique_id, self.landfill_state, max(self.landfill_cost -
                 self.landfill_revenue, 0), self.landfill_cost,
                 self.landfill_revenue))
            self.model.variables_landfills_tr[self.landfill_type].append(
                (self.unique_id, self.landfill_name, max(self.landfill_cost -
                 self.landfill_revenue, 0), self.landfill_cost,
                 self.landfill_revenue))
        else:
            self.model.variables_landfills[self.landfill_type].append(
                (self.unique_id, self.landfill_state, np.nan,
                 np.nan, np.nan))
            self.model.variables_landfills_tr[self.landfill_type].append(
                (self.unique_id, self.landfill_name, np.nan,
                 np.nan, np.nan))
        self.model.landfill_remaining_cap[self.landfill_state] += \
            self.remaining_capacity
        self.model.state_blade_waste[self.landfill_state] += self.blade_waste
        self.model.average_eol_costs[self.landfill_type] += \
            self.landfill_cost / self.model.landfill_count

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
