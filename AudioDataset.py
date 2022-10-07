import torch
import torchaudio
import random

from torch.utils.data import Dataset, DataLoader

from pathlib import Path
import os

from Augmentation import Augmentor
from audiomentations import Compose

import numpy as np


class AudioDataset(Dataset):

    def __init__(self,
                 audio_paths,
                 specTransformList=None,
                 audioTransformList=None):

        self.specTransformList = specTransformList

        self.audioAugment = Compose(
            audioTransformList) if audioTransformList else None

        self.audio_paths = audio_paths

        self.Augmentor = Augmentor()

    def __len__(self):
        return len(self.audio_paths)

    def __getitem__(self, idx):

        path, filename = os.path.split(self.audio_paths[idx])

        title, _ = os.path.splitext(filename)

        fsID, classID, occurrenceID, sliceID = [
            int(n) for n in title.split('-')
        ]

        waveform, sample_rate = self.Augmentor.pad_trunc(
            self.Augmentor.resample(
                self.Augmentor.rechannel(torchaudio.load(
                    self.audio_paths[idx]))))

        if self.audioAugment:
            waveform = self.audioAugment(waveform.numpy(), 44100)
            if not torch.is_tensor(waveform):
                waveform = torch.from_numpy(waveform)

        spectrogram = torchaudio.transforms.Spectrogram()

        spectrogram_tensor = (spectrogram(waveform) + 1e-12).log2()

        assert spectrogram_tensor.shape == torch.Size(
            [1, 201,
             883]), f"Spectrogram size mismatch! {spectrogram_tensor.shape}"

        if self.specTransformList:

            for transform in self.specTransformList:

                spectrogram_tensor = transform(spectrogram_tensor)

        return [spectrogram_tensor, classID]
