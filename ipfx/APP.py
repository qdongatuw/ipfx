import os
from tkinter import filedialog
import numpy as np
import pandas as pd
import pyabf
from feature_extractor import SpikeFeatureExtractor, SpikeTrainFeatureExtractor
import subthresh_features as sbth


filetypes = [('ABF Files', '*.abf')]
files = filedialog.askopenfilenames(filetypes=filetypes)

sfe = SpikeFeatureExtractor(filter=2)
spte = SpikeTrainFeatureExtractor(start=0, end=16000)

out_folder = r'C:\Users\dongq\OneDrive\mouse patch-seq\result'
out_csv = r'C:\Users\dongq\OneDrive\mouse patch-seq\result\test.csv'

name_list = [os.path.basename(i) for i in files]
df = pd.DataFrame()

for file in files:
    file_name = os.path.basename(file)
    f = pyabf.ABF(file)

    if f.nOperationMode == 5 and f.sweepCount > 3:   # multi-sweeps
        folder = out_folder + '\\' + f.abfID
        if not os.path.exists(folder):
            os.mkdir(folder)

        if f.sweepUnitsC == 'pA':   # current clamp

            sampling_rate = f.sampleRate
            temp_result_list = []

            rmp = []
            rin = []
            tau = []
            sag = []
            vol_deflection = []

            f.setSweep(0)
            first_epoc = f.sweepEpochs
            f.setSweep(1)
            second_epoc = f.sweepEpochs
            dif = np.asarray(second_epoc.levels) - np.asarray(first_epoc.levels)

            step = dif != 0
            start = np.asarray(first_epoc.p1s)[step][0]
            end = np.asarray(first_epoc.p2s)[step][0]

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
                current = f.sweepEpochs.levels[step][0]
                sptft['injected current (pA)'] = current
                temp_result_list.append((ft, sptft))
            
            with open(f'{folder}/result.txt', mode='w', encoding='utf-8') as result_txt_file:
                for i_result in temp_result_list:
                    result_txt_file.write(str(i_result[1]))
                    result_txt_file.write('\n')

            for i_result in temp_result_list:
                if i_result[1]['avg_rate'] > 0:
                    new_df = i_result[0].mean(numeric_only=True).to_frame().T
                    new_df.insert(0, 'File', file_name)
                    break
            fire_pattern_df = None
            for i_result in temp_result_list:
                if 'adapt' in i_result[1] and i_result[1]['adapt'] > 0:
                    temp_dict = {i: [i_result[1][i]] for i in i_result[1]} 
                    fire_pattern_df = pd.DataFrame(temp_dict)
                    fire_pattern_df.insert(0, 'File', file_name)
                    break
            if fire_pattern_df is not None:
                temp_df1 = pd.merge(new_df, fire_pattern_df, on='File')
            else:
                temp_df1 = new_df
            firing_rate_list = dict()
            firing_rate_list['File'] = [file_name]
            firing_rate_list['sampling rate'] = [sampling_rate]
            for i_result in temp_result_list:
                current = i_result[1]['injected current (pA)']
                rate = i_result[1]['avg_rate'] * sampling_rate
                firing_rate_list[f'{current} pA'] = [rate]
            rate_df = pd.DataFrame(firing_rate_list)
            temp_df2 = pd.merge(temp_df1, rate_df, on='File')
            df = pd.concat([df, temp_df2])
df.to_csv(out_csv, index=False)

            
            
            