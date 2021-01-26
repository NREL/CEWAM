# -*- coding:utf-8 -*-
"""
Created on December 31 2020

@author Julien Walzberg - Julien.Walzberg@nrel.gov

Run - Circular Economy Wind Agent-based Model (CEWAM)
This module run the model according to user inputs.
"""

# TODO:
#  1) create a class to hold all function for runs?
#  2) create a test file with a test for a few steps and known results to
#  reproduce


from Wind_ABM_Model import *
import time


for j in range(1):
    t0 = time.time()
    model = WindABM(temporal_scope={
                     'pre_simulation': 2000, 'simulation_start': 2020,
                     'simulation_end': 2051})
    for i in range((model.temporal_scope['simulation_end'] -
                    model.temporal_scope['simulation_start'])):
        model.step()
    results_model = model.data_collector.get_model_vars_dataframe()
    results_agents = model.data_collector.get_agent_vars_dataframe()
    results_model.to_csv("Results_model.csv")
    results_agents.to_csv("Results_agents.csv")
    t1 = time.time()
    print(t1 - t0)
