import numpy as np
import matplotlib.pyplot as plt
import pyabf
import os
import pandas as pd

file = r"C:\Users\dongq\OneDrive\mouse patch-seq\MBD1 project\2023_03_27_0088.abf"
f = pyabf.ABF(file)

print(f"command units: {f.sweepUnitsC}")

f.setSweep(0)
first_epoc = f.sweepEpochs
f.setSweep(1)
second_epoc = f.sweepEpochs
dif = np.asarray(second_epoc.levels) - np.asarray(first_epoc.levels)

step = np.where(dif != 0)
start = np.asarray(first_epoc.p1s)[step][0]
end = np.asarray(first_epoc.p2s)[step][0]

print(start, end)

sampling_rate = f.sampleRate

import qc_features as qc

v, t, i = f.sweepC[:start-1], f.sweepX[:start-1], f.sweepY[:start-1]

result = qc.measure_seal(v, i, t)
print(result)


