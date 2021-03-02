# -*- coding:utf-8 -*-
"""
Created on January 11 2021

@author Julien Walzberg - Julien.Walzberg@nrel.gov

Landfill - Circular Economy Wind Agent-based Model (CEWAM)
This module contains the Landfill class. Landfills make several
decisions, for instance, to accept Wind Blades or not.
"""

# Notes:
# Remove unused library imports


from mesa import Agent

# TODO: the percentage for regulator to act should be determined from EPA
#  database looking at the landfill that already closed and what was their
#  amount of waste left / the initial capacity
#  Use the WBJ Landfills 2020 in C:\Users\jwalzber\Documents\Winter21\
#  Wind_ABM\Modeling\Data\LandfillDatabases to determine some info on the
#  landfill (e.g., if they accept blade or not (e.g., we can consider as
#  construction and demolition waste) and determine in each state the share of
#  landfill that accept wind blade as waste (weight by the capacity of each
#  landfill in the calculation). Use the EPA database for the rest if need be
#  (check if all the information in the EPA database can be found in WBJ
#  Landfills 2020 database)


class Landfill(Agent):
    def __init__(self, unique_id, model, **kwargs):
        super().__init__(unique_id, model)
        """
        Creation of new agent
        """
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.internal_clock = 0

        # TODO: replace mock-up values by actual values and function of
        #  landfill agents
        self.landfill_type = list(self.model.landfills.keys())[0]
        self.landfill_state = self.model.landfill_state_list.pop()
        self.landfill_cost = self.model.landfill_costs[self.landfill_state]
        self.model.variables_landfills[self.landfill_type].append(
            (self.unique_id, self.landfill_state, self.landfill_cost))
        self.closure = False
        self.model.waste_rec_land[self.unique_id] = 0

    def mock_up(self):
        pass

    @staticmethod
    def mock_up_landfill_state(dic_to_choose_from):
        pass

    @staticmethod
    def closure_update(other_regulations, landfill_state):
        if other_regulations[landfill_state]['landfill']:
            closure = True
        else:
            closure = False
        return closure

    def update_agent_variables(self):
        """
        Update instance (agent) variables
        """
        self.closure = self.closure_update(
            self.model.other_regulations_enacted, self.landfill_state)

    def report_agent_variables(self):
        """
        Report instance (agent) variables
        """
        if not self.closure:
            self.model.variables_landfills[self.landfill_type].append(
                (self.unique_id, self.landfill_state, self.landfill_cost))

    def step(self):
        """
        Evolution of agent at each step. As Mesa is not built for having
        multiple scheduler, step needs to pass the global scheduler.
        """
        if self.internal_clock == self.model.clock:
            self.mock_up()
            self.update_agent_variables()
            self.report_agent_variables()
            self.internal_clock += 1
        else:
            pass
