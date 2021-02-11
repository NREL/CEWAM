# -*- coding:utf-8 -*-
"""
Created on December 31 2020

@author Julien Walzberg - Julien.Walzberg@nrel.gov

Run - Circular Economy Wind Agent-based Model (CEWAM)
This module run the model according to user inputs.
"""

# TODO:
#  1) create a class to hold all function for runs?
#  2) Consider value added of using df['Dictionary'].apply(pd.Series)] to
#  transform reported dictionary in pandas columns (Should it be a
#  post-simulation treatment or not?) when creating data frames from data
#  collector
#  3) To report by state and eol pathway - use a nested dictionary then use
#  example code below to unpack (either here or in post-simulation):
#  dct = {'Colorado': {'ce': 2, 'landfill': 5}, 'California': {'ce': 0,
#  'landfill': 10}, 'Washington': {'ce': 4, 'landfill': 3}}
#  v = pd.DataFrame(dct).stack()
#  w = (pd.DataFrame(v.tolist(), index=v.index)
#    .stack()
#    .unstack(0)
#    .reset_index(level=1, drop=True)
#    .rename_axis('State')
#    .reset_index())
#  w.head()


from Wind_ABM_Model import *
import time


def run_model(number_run, number_steps, model_instance):
    """
    Run model and collect outputs at each time steps. Creates a new file for
    each run. Use a new seed for random generation at each run.
    :param number_run number of replicates for one model configuration
    :param number_steps duration of the simulation(s) in years
    :param model_instance: model and its configuration for the simulation(s)
    """
    for j in range(number_run):
        t0 = time.time()
        model_instance.seed = j
        model_instance.temporal_scope['simulation_end'] = (2020 + number_steps)
        for i in range((model_instance.temporal_scope['simulation_end'] -
                        model_instance.temporal_scope['simulation_start'])):
            model_instance.step()
        results_model = \
            model_instance.data_collector.get_model_vars_dataframe()
        results_agents = \
            model_instance.data_collector.get_agent_vars_dataframe()
        results_model.to_csv("results\\Results_model_run_%s.csv" % j)
        results_agents.to_csv("results\\Results_agents_run_%s.csv" % j)
        t1 = time.time()
        print(t1 - t0)


# default temporal scope: 2020-2051
model = WindABM()

run_model(1, 31, model)
