# -*- coding:utf-8 -*-
"""
Created on January 11 2021

@author Julien Walzberg - Julien.Walzberg@nrel.gov

Recycler - Circular Economy Wind Agent-based Model (CEWAM)
This module contains the Recycler class. Recyclers make several
decisions, for instance, what type of recycling to perform.
"""

# Notes:
# Remove unused library imports


from mesa import Agent
import random

# TODO: separate pre-processing (e.g., done by Veolia) and actual co-processing
#  (done by cement factories) in terms of activity and agents. In this way
#  the number (and locations) of co-processing facilities can be different
#  from the number of cement factories

# TODO: lifetime extension: Continue HERE:
#  1) assign revenue for recycler
#  2) assign costs and revenue for lifetime extension in Developer


class Recycler(Agent):
    def __init__(self, unique_id, model, **kwargs):
        super().__init__(unique_id, model)
        """
        Creation of new agent
        """
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.internal_clock = 0

        # TODO: replace mock-up values below by a function to determine
        #  recyclers state
        self.recycler_state = self.mock_up_random_state(
            self.model.growth_rates)
        self.recycler_type = self.model.roulette_wheel_choice(
            self.model.recyclers, sum(self.model.recyclers.values()),
            True, []).pop()
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

    def mock_up(self):
        pass

    @staticmethod
    def mock_up_random_state(dic_to_shuffle):
        list_to_shuffle = list(dic_to_shuffle.keys())
        random.shuffle(list_to_shuffle)
        pick = list_to_shuffle[0]
        return pick

    def update_agent_variables(self):
        """
        Update instance (agent) variables
        """
        # TODO: build learning effect function and update recycler costs
        #  instead of having self.init_recycler_cost
        self.recycler_cost = self.init_recycler_cost
        self.model.variables_recyclers[self.recycler_type].append(
            (self.unique_id, self.recycler_state, self.recycler_cost))

    def step(self):
        """
        Evolution of agent at each step. As Mesa is not built for having
        multiple scheduler, step needs to pass the global scheduler.
        """
        if self.internal_clock == self.model.clock:
            self.mock_up()
            self.update_agent_variables()
            self.internal_clock += 1
        else:
            pass
