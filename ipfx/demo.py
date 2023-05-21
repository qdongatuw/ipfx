import numpy as np
import matplotlib.pyplot as plt
import pyabf
import os
import pandas as pd

file = r"C:\Users\dongq\OneDrive\mouse patch-seq\MBD1 project\2023_04_01_0101.abf"
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

from feature_extractor import SpikeFeatureExtractor, SpikeTrainFeatureExtractor
sfe = SpikeFeatureExtractor(filter=2)
spte = SpikeTrainFeatureExtractor(start=start/sampling_rate, end=end/sampling_rate)

import subthresh_features as sbth

rmp = []
tau = []
sag = []

t_set = []
i_set = []
v_set = []

temp_result_list = []
flag_spike = False
for index in f.sweepList:
    f.setSweep(index)
    t = f.sweepX
    v = f.sweepY
    i = f.sweepC

    if f.sweepUnitsY == f.sweepUnitsC:
        v = v/20
    current = np.asarray(f.sweepEpochs.levels)[step][0]

    rmp.append(np.median(v[np.where(i == 0)]))
    if current < 0:
        print(start/sampling_rate, (end-2)/sampling_rate)
        baseline_interval = min(start-0.01, 0.1)
        tau.append(sbth.time_constant(t=t, v=v, i=i, start=start/sampling_rate, end=(end-2)/sampling_rate, baseline_interval=baseline_interval))
        sag.append(sbth.sag(t=t, v=v, i=i, start=start/sampling_rate, end=end/sampling_rate, baseline_interval=baseline_interval))
        t_set.append(t)
        i_set.append(i)
        v_set.append(v)
    
    if current == 0:
        t_set.append(t)
        i_set.append(i)
        v_set.append(v)

    ft = sfe.process(t, v, i)
    # ft.to_csv(f'{index}.csv', index=False)
    sptft= spte.process(t=t, v=v, i=i, spikes_df=ft)
    print(sptft)
    
    sptft['current'] = current
    temp_result_list.append((ft, sptft))
