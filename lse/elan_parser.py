import os
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from pympi import Eaf


def find_eaf_files(root_dir: str) -> [str]:
    """Collect all ELAN files for the VGT corpus.
    Hidden files are ignored.

    :param root_dir: The root directory under which the ELAN files are located.
    :return: A list of absolute paths to the ELAN files."""
    return sorted(filter(lambda p: not os.path.basename(p).startswith('.'), Path(root_dir).rglob('*.eaf')))


@dataclass
class ParticipantURL:
    """Links a participant ID with the URI to the corresponding video file in the corpus.

    The participantID field indicates the ID within a video file (signer 1 or signer 2).
    The participantName field indicates the name of the participant over the entire corpus.
    The uri is the path to the video file in which this participant is recorded in this session."""
    participant_ID: str
    participant_name: str
    uri: str


@dataclass
class GlossAnnotation:
    gloss: str
    start_ms: int
    end_ms: int


@dataclass
class Metadata:
    filename: str
    participant: str


@dataclass
class Videos:
    source_video: str
    sample_video: str


@dataclass
class ISLRSample:
    id: int
    gloss: GlossAnnotation
    metadata: Metadata
    videos: Videos


class LSEEaf:
    """Contains all the relevant information for the LSE corpus present in .eaf files."""

    def __init__(self, eaf_path: str, video_root: str):
        """Create a new LSEEaf instance.

        :param eaf_path: The path to the .eaf file.
        :param video_root: The path to where the videos are located on the machine on which this script is run."""
        self._eaf_path = eaf_path
        try:
            self._eaf = Eaf(str(self._eaf_path))
        except Exception as e:
            raise ValueError(f'Unable to parse eaf file {self._eaf_path}: {e}')
        self._video_root = video_root

    def collect_islr_samples(self, start_ID: int) -> [ISLRSample]:
        """Parse the samples.
        We collect all dominant hand glosses.

        :param start_ID: We will begin with this ID.
        :return: A list of samples."""
        gloss_rh_tier = f'Glossa mà activa S1'

        samples = []

        media = self._eaf.media_descriptors[0]
        url = media['MEDIA_URL']
        participant = url.split('-')[2]  # The video URL contains the participant ID.

        try:
            for gloss_annotation in self._eaf.get_annotation_data_for_tier(gloss_rh_tier):
                if gloss_annotation[0] >= gloss_annotation[1]:  # start >= end: invalid.
                    continue

                sample = ISLRSample(start_ID,
                                    GlossAnnotation(gloss_annotation[2], gloss_annotation[0], gloss_annotation[1]),
                                    Metadata(str(self._eaf_path), participant),
                                    Videos(*url.split(os.sep)[-1:], f'{os.path.basename(self._eaf_path)}_{start_ID}.mp4'))
                samples.append(sample)
                start_ID += 1
        except KeyError:  # GlosRH tier not found.
            pass

        return samples
