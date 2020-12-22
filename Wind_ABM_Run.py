from Wind_ABM_Model import *
import time

for j in range(1, 11):
    t0 = time.time()
    for i in range(30):
        WindABM(num_consumers=(2000*j)).step()
    t1 = time.time()
    print(j, (t1 - t0))

