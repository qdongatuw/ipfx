from tkinter import filedialog
import numpy as np
import matplotlib.pyplot as plt
from neo.io import AxonIO

from feature_extractor import SpikeFeatureExtractor, SpikeTrainFeatureExtractor


files = filedialog.askopenfilenames()

for file in files:
    f = AxonIO(file)
    blocks = f.read()
    bl = blocks[0]

    num_episodes = f.segment_count(0)

    if num_episodes < 3:
        continue
    
    sampling_rate = f.get_signal_sampling_rate(0)
    block_count = f.block_count()
    segs = bl.segments

    sfe = SpikeFeatureExtractor(filter=2)
    spte = SpikeTrainFeatureExtractor(start=0, end=16000)