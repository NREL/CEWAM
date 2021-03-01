# -*- coding:utf-8 -*-
"""
Created on December 31 2020

@author Julien Walzberg - Julien.Walzberg@nrel.gov

Run - Circular Economy Wind Agent-based Model (CEWAM)
This module run the model according to user inputs.
"""

# TODO:
#  0) Change panda frame output to transform dictionary in independent
#  variables and time how long it take (if too long I can just do it
#  externally)
#  1) Consider value added of using df['Dictionary'].apply(pd.Series)] to
#  transform reported dictionary in pandas columns (Should it be a
#  post-simulation treatment or not?) when creating data frames from data
#  collector
#  2) To report by state and eol pathway - use a nested dictionary then use
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
#  4) I can compile file before running - use: "python -m nuitka
#  Wind_ABM_Run.py --include-module=Wind_ABM_Model
#  --include-module=Wind_ABM_WindPlantOwner [and other modules]" in Anaconda
#  prompt

from Wind_ABM_Model import *
import time


class WindABMRun:
    def __init__(self, number_run=1, number_steps=31, model_in=WindABM,
                 **kwargs):
        """
        Set up the parameters for the model runs
        :param number_run: number_run number of replicates for one model
        configuration - default is 1
        :param number_steps: duration of the simulation(s) in years - default
        is 31
        :param model_in: model - default is the CE Wind ABM
        :param kwargs: configuration of the model for the simulation(s)
        (parameters to set up the model) - default is empty
        """
        self.number_run = number_run
        self.number_steps = number_steps
        self.model_in = model_in
        self.kwargs = kwargs
        self.model_instance = None

    def set_up_run_model(self):
        """
        Set up the run model which collect outputs at each time steps.
        Creates a new file for each run. Use a new seed for random generation
        at each run.
        """
        for j in range(self.number_run):
            t0 = time.time()
            self.model_instance = self.model_in(seed=j ,temporal_scope={
                'pre_simulation': 2000, 'simulation_start': 2020,
                'simulation_end': (2020 + self.number_steps)})
            for key, value in self.kwargs.items():
                setattr(self.model_instance, key, value)
            for i in range(
                    (self.model_instance.temporal_scope['simulation_end'] -
                     self.model_instance.temporal_scope['simulation_start'])):
                self.model_instance.step()
            results_model = \
                self.model_instance.data_collector.get_model_vars_dataframe()
            results_agents = \
                self.model_instance.data_collector.get_agent_vars_dataframe()
            results_model.to_csv("results\\Results_model_run_%s.csv" % j)
            results_agents.to_csv("results\\Results_agents_run_%s.csv" % j)
            t1 = time.time()
            print('Replicate', (j + 1), 'out of', self.number_run,
                  ' with run time of:', t1 - t0)

    def run_model(self):
        """Run the set up model"""
        self.set_up_run_model()


# Comment line below when running WindWBMRun tests
WindABMRun().run_model()
