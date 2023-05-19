import os
from tkinter import filedialog
import numpy as np
import pandas as pd
import pyabf
from feature_extractor import SpikeFeatureExtractor, SpikeTrainFeatureExtractor


filetypes = [('ABF Files', '*.abf')]
files = filedialog.askopenfilenames(filetypes=filetypes)

sfe = SpikeFeatureExtractor(filter=2)
spte = SpikeTrainFeatureExtractor(start=0, end=16000)

out_folder = r'C:\Users\dongq\OneDrive\mouse patch-seq\result'

name_list = [os.path.basename(i) for i in files]
df = pd.DataFrame({'File': name_list})

for file in files:
    f = pyabf.ABF(file)

    if f.nOperationMode == 5:   # multi-sweeps
        folder = out_folder + '\\' + f.abfID
        if not os.path.exists(folder):
            os.mkdir(folder)

        if f.sweepUnitsC == 'pA':   # current clamp

            sampling_rate = f.sampleRate
            temp_result_list = []
            flag_spike = False
            for index in f.sweepList:
                f.setSweep(index)
                t = f.sweepX
                v = f.sweepY
                i = f.sweepC

                if f.sweepUnitsY == f.sweepUnitsC:
                    v = v/20
                ft = sfe.process(t, v, i)
                ft.to_csv(f'{folder}/{index}.csv', index=False)
                sptft= spte.process(t=t, v=v, i=i, spikes_df=ft)
                
                temp_result_list.append((ft, sptft))
                
                if not flag_spike:
                    if sptft['avg_rate'] > 0:
                        new_df = ft.mean().to_frame().T
                        new_df.insert(0, 'File', os.path.basename(file))
                        flag_spike = True

            