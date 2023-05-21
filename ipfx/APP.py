import os
from datetime import datetime
import tkinter as tk
from tkinter import filedialog
import numpy as np
import pandas as pd
import pyabf
from feature_extractor import SpikeFeatureExtractor, SpikeTrainFeatureExtractor
import subthresh_features as sbth
import qc_features as qc


root = tk.Tk()
root.withdraw()

selected_folder = filedialog.askdirectory()

file_paths = []

for root_dir, dirs, files in os.walk(selected_folder):
    for file in files:
        if file.lower().endswith('.abf'):
            file_paths.append(os.path.join(root_dir, file))

print(len(file_paths))

# filetypes = [('ABF Files', '*.abf')]
# files = filedialog.askopenfilenames(filetypes=filetypes)


out_folder = r'C:\Users\dongq\OneDrive\mouse patch-seq\result'
out_csv = fr'C:\Users\dongq\OneDrive\mouse patch-seq\result\{datetime.now().strftime("%Y-%m-%d-%H-%M")}.csv'

df = pd.DataFrame()

for file in file_paths:
    file_name = os.path.basename(file)
    print(file_name)
    f = pyabf.ABF(file)

    if f.nOperationMode == 5 and f.sweepCount > 3:   # multi-sweeps
        folder = out_folder + '\\' + f.abfID
        if not os.path.exists(folder):
            os.mkdir(folder)
        
        f.setSweep(0)
        first_epoc = f.sweepEpochs
        f.setSweep(1)
        second_epoc = f.sweepEpochs
        dif = np.asarray(second_epoc.levels) - np.asarray(first_epoc.levels)

        step = dif != 0
        start = np.asarray(first_epoc.p1s)[step][0]
        end = np.asarray(first_epoc.p2s)[step][0]

        if f.sweepUnitsC == 'pA':   # current clamp

            sampling_rate = f.sampleRate
            temp_result_list = []

            rmp = []
            tau = []
            sag = []

            t_set = []
            i_set = []
            v_set = []

            sfe = SpikeFeatureExtractor(filter=2)
            spte = SpikeTrainFeatureExtractor(start=start/sampling_rate, end=end/sampling_rate)

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
                    baseline_interval = min(start/(sampling_rate*2), 0.1)
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
                ft.to_csv(f'{folder}/{index}.csv', index=False)
                sptft= spte.process(t=t, v=v, i=i, spikes_df=ft)
                sptft['injected current (pA)'] = current
                temp_result_list.append((ft, sptft))

            rin = sbth.input_resistance(t_set=t_set, i_set=i_set, v_set=v_set, start=start/sampling_rate, end=end/sampling_rate)


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
                rate = i_result[1]['avg_rate']
                firing_rate_list[f'{current} pA'] = [rate]
            rate_df = pd.DataFrame(firing_rate_list)
            temp_df2 = pd.merge(temp_df1, rate_df, on='File')

            sub_df = pd.DataFrame({'File': [file_name], 
                                   'RMP': [np.mean(rmp)],
                                   'time constant (sec)': [np.mean(tau)], 
                                   'input resistance (Mo)': [rin],
                                   'sag ratio': [np.mean(sag)]})
            
            temp_df3 = pd.merge(temp_df2, sub_df, on='File')

            df = pd.concat([df, temp_df3])


        if f.sweepUnitsC == 'mV':
            # QC
            rin_v = []
            r_access = []

            ina = dict()

            for index in f.sweepList:
                f.setSweep(index)
                v, t, i = f.sweepC[:start-1], f.sweepX[:start-1], f.sweepY[:start-1]
                holding_current = np.median(i[np.where(v == f.sweepEpochs.levels[0])])
                rin_v.append(qc.measure_input_resistance(v, i, t))
                r_access.append(qc.measure_initial_access_resistance(v, i, t))

                v_step = np.asarray(f.sweepEpochs.levels)[step][0]
                i_peak = np.min(f.sweepY[start:end]) - holding_current

                
                ina[f'{v_step} mV'] = i_peak
            qc_df = pd.DataFrame({'File': [file_name],
                                  'Input Resistance(v_clamp)': [np.mean(rin_v)],
                                  'Access resistance': [np.mean(r_access)]})
            for i in ina:
                qc_df[i] = [ina[i]]
            df = pd.concat([df, qc_df])



df.to_csv(out_csv, index=False)

            
            
            