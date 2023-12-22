import glob
import os
import random

import PIL
import cv2
import torch


class Dataset(torch.utils.data.Dataset):
    def __init__(self, root_dir, transforms, job):
        super().__init__()

        self.root_dir = root_dir
        all_samples = sorted(glob.glob(os.path.join(root_dir, '*.mp4')))

        train_lengths = int(0.7 * len(all_samples))
        val_lengths = int(0.1 * len(all_samples))
        test_lengths = len(all_samples) - train_lengths - val_lengths

        train, validation, test = torch.utils.data.random_split(all_samples,
                                                                [train_lengths, val_lengths, test_lengths])
        if job == 'train':
            self.samples = train
        elif job == 'validate':
            self.samples = validation
        else:
            assert job == 'test'
            self.samples = test

        self.transforms = transforms

    def __getitem__(self, item):
        sample_index = item // 100
        # Returns a random frame from the video at given index.
        cap = cv2.VideoCapture(self.samples[sample_index])
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # We take an index > 25 and < len(frames) - 26 to make sure that we get a good view of the face,
        # and not of someone still moving in or out of the frame (who may also be the wrong person).
        # 25 because that corresponds to 1 second.
        if frame_count >= 50:
            index = random.randint(25, frame_count - 26)
        else:
            # If not possible, just take a random frame...
            index = random.randint(0, frame_count - 1)
        cap.set(cv2.CAP_PROP_POS_FRAMES, index)
        success, frame = cap.read()
        assert success

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = PIL.Image.fromarray(frame)

        frame = self.transforms(frame)

        # Sample filename structure: FILENAME__LANGUAGE_INDEX
        language = self.samples[sample_index].split('__')[1].split('_')[0]
        label = 1 if language == 'VGT' else 0

        return frame, torch.tensor(label, dtype=torch.float32)

    def __len__(self):
        # Returns the number of clips, not the number of actual samples.
        return len(self.samples) * 100
