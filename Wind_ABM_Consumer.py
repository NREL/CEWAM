# Notes:
# In the event of negative profit (loss), the wind farm owner would need to
# subsidize (pay) to process the end-of-life material. If this is more
# expensive than solid waste disposal, most wind farm owners will
# (and currently do) choose the least-cost option: solid waste disposal.
# You can use Liu et al. 2019 to include energy net impact results as a first
# approximation for adding environmental information to the model
# Think about using the machine learning metamodel to calibrate the ABM
# It takes a lot of time to go through the model schedule... If possible,
# try to avoid it!!!

from mesa import Agent
import numpy as np
import random
from collections import OrderedDict
from scipy.stats import truncnorm
import operator
from math import *
import time


class Consumers(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.unit = 1

    def give_unit(self):
        neighbors_nodes = self.model.grid.get_neighbors(self.pos,
                                                        include_center=False)
        obtainer = random.choice(neighbors_nodes)
        if self.unit > 0:
            self.unit -= 1
            #for agent in self.model.schedule.agents:
             #   if agent.unique_id == obtainer:
              #      agent.unit += 1
        print(self.unique_id)

    def step(self):
        """
        Evolution of agent at each step
        """
        self.give_unit()
