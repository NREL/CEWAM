# -*- coding:utf-8 -*-
"""
Created on January 11 2021

@author Julien Walzberg - Julien.Walzberg@nrel.gov

Regulator - Circular Economy Wind Agent-based Model (CEWAM)
This module contains the Regulator class. Regulators make several
decisions, for instance, to ban some landfills from accepting blades.
"""

# Notes:
# Remove unused library imports


from mesa import Agent

# TODO:
#  1) build regulation enacting
#  2) the percentage for regulator to act should be determined from EPA
#  database looking at the landfill that already closed and what was their
#  amount of waste left / the initial capacity


class Regulator(Agent):
    def __init__(self, unique_id, model, **kwargs):
        super().__init__(unique_id, model)
        """
        Creation of new agent
        """
        for key, value in kwargs.items():
            setattr(self, key, value)
        # Variables internal to the class -
        self.internal_clock = self.model.clock
        self.regulator_state = self.model.regulator_states_list.pop()
        self.regulations_enacted = self.model.initial_dic_from_key_list(
            self.model.eol_pathways, False)
        self.bans = self.model.initial_dic_from_key_list(
            self.model.eol_pathways, False)
        self.other_regulations = self.model.initial_dic_from_key_list(
            self.model.eol_pathways, False)
        self.threshold = self.model.symetric_triang_distrib_draw(
            self.model.reg_landfill_threshold[0],
            self.model.reg_landfill_threshold[1])

    @staticmethod
    def initiate_landfill_ban(state, landfill_remaining_cap,
                              init_land_capacity, threshold, safe_div):
        percentage_landfills_remain = safe_div(landfill_remaining_cap[state],
                                               init_land_capacity[state])
        if percentage_landfills_remain < (1 - threshold):
            return True
        else:
            return False

    def update_agent_variables(self):
        """
        Update instance (agent) variables
        """
        self.bans['landfill'] = self.initiate_landfill_ban(
            self.regulator_state, self.model.landfill_remaining_cap,
            self.model.init_land_capacity, self.threshold, self.model.safe_div)
        self.regulations_enacted = self.model.boolean_dic_based_on_dicts(
            self.regulations_enacted, True, True, self.bans,
            self.other_regulations)

    def report_agent_variables(self):
        """
        Report instance (agent) variables
        """
        for key in self.regulations_enacted.keys():
            self.model.regulations_enacted[key][self.regulator_state] = \
                self.regulations_enacted[key]
            self.model.bans_enacted[self.regulator_state][key] = self.bans[key]
            self.model.other_regulations_enacted[
                self.regulator_state][key] = self.other_regulations[key]

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
