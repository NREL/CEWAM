# -*- coding:utf-8 -*-
"""
Created on December 31 2020

@author Julien Walzberg - Julien.Walzberg@nrel.gov

Test functions in Wind_ABM_WIndPlantOwner
"""


from unittest import TestCase
from Wind_ABM_Model import WindABM
from Wind_ABM_WindPlantOwner import WindPlantOwner
from mesa.time import RandomActivation
from mesa.space import NetworkGrid


class TestWindPlantOwner(TestCase):
    def test_sum_agent_variable_once_or_every_step(self):
        """Function can't be formally tested here"""
        pass

    def test_wind_power_capacity_state_distribution(self):
        """Verify that capacities are distributed as should be within the US"""
        schedule = WindABM().schedule_wpo
        test_uswtdb = WindABM().uswtdb.drop(['p_name'], axis=1)
        test_uswtdb = test_uswtdb.groupby(['t_state']).sum()
        value = []
        test_score = []
        for index, row in test_uswtdb.iterrows():
            test_sum = 0
            for a in schedule.agents:
                if a.t_state == index:
                    test_sum += a.p_cap
            if test_sum == row['p_cap']:
                test_score.append(True)
            else:
                test_score.append(False)
            value.append(True)
        self.assertCountEqual(value, test_score)

    def test_compute_mass_conv_factor(self):
        """Verify that conversion factor is computed correctly"""
        rotor_diameter = 20
        coefficient = 0.5
        power = 2
        blades_per_rotor = 3
        t_cap = 10
        result = coefficient * (rotor_diameter / 2)**power * \
            blades_per_rotor / t_cap
        unique_id = 0
        test_result = \
            WindPlantOwner(unique_id, WindABM()).compute_mass_conv_factor(
                rotor_diameter, coefficient, power, blades_per_rotor, t_cap)
        self.assertEqual(result, test_result)

    def test_update_agent_variables(self):
        """Function can't be formally tested here"""
        pass

    def test_remove_agent(self):
        """Test that agent is removed"""
        test_model = WindABM()
        num_agents = len(test_model.schedule_wpo.agents)
        agent = test_model.schedule_wpo.agents[0]
        agent.p_cap_waste = 0
        agent.remove_agent()
        test_result = len(test_model.schedule_wpo.agents)
        result = num_agents - 1
        self.assertEqual(test_result, result)

    def test_step(self):
        """Test that the wpo agents run steps without errors"""
        model = WindABM()
        agent = WindPlantOwner(0, model)
        steps = 1
        agent.step()
        clock = agent.internal_clock
        self.assertEqual(steps, clock)
