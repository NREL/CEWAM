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
        self.model.recycler_states[self.recycler_type].append(
            self.recycler_state)

    def mock_up(self):
        pass

    @staticmethod
    def mock_up_random_state(dic_to_shuffle):
        list_to_shuffle = list(dic_to_shuffle.keys())
        random.shuffle(list_to_shuffle)
        pick = list_to_shuffle[0]
        return pick

    def step(self):
        """
        Evolution of agent at each step. As Mesa is not built for having
        multiple scheduler, step needs to pass the global scheduler.
        """
        if self.internal_clock == self.model.clock:
            self.mock_up()
            self.internal_clock += 1
        else:
            pass
