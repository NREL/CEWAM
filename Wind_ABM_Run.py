# -*- coding:utf-8 -*-
"""
Created on December 31 2020

@author Julien Walzberg - Julien.Walzberg@nrel.gov

Run - Circular Economy Wind Agent-based Model (CEWAM)
This module run the model according to user inputs.
"""


from Wind_ABM_Model import *
import time


for j in range(1):
    t0 = time.time()
    model = WindABM()
    for i in range(2):
        model.step()
    t1 = time.time()
    print(j, (t1 - t0))

