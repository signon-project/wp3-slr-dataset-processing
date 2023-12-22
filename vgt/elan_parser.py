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
    participant_name: str
    participant_ID: str


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


class VGTEaf:
    """Contains all the relevant information for the VGT corpus present in .eaf files."""

    def __init__(self, eaf_path: str, video_root: str):
        """Create a new VGTEaf instance.

        :param eaf_path: The path to the .eaf file.
        :param video_root: The path to where the videos are located on the machine on which this script is run."""
        self._eaf_path = eaf_path
        try:
            self._eaf = Eaf(str(self._eaf_path))
        except Exception as e:
            raise ValueError(f'Unable to parse eaf file {self._eaf_path}: {e}')
        self._video_root = video_root
        self._participants = None

    def is_valid(self):
        """Certain files in the VGT Corpus are invalid. These are files that contain media URLs that are
        inaccessible, e.g., on the annotator's local machine."""
        media = self._eaf.media_descriptors
        for entry in media:
            url = entry['MEDIA_URL']
            # Only keep those files that are linked to the videos we have.
            full_path = os.path.join(self._video_root, *url.split(os.sep)[-2:])
            if not full_path.endswith('all.mp4') and (
                    not os.path.isfile(full_path) or 'Volumes/corpusvgt/Videomateriaal/CVGT' not in url):
                return False
        return True

    def participant_ids(self) -> dict:
        """Get the participant IDs in this file.

        :return: A dictionary with ID as key and ParticipantURL as value."""
        if self._participants is None:
            file_participant_IDs = []
            file_participant_names = []
            urls = []
            media = self._eaf.media_descriptors
            for entry in media:
                url = entry['MEDIA_URL']
                basename = os.path.basename(url)
                pid = basename.split('_')[-1].replace('.mp4', '')
                if pid != 'all':
                    file_participant_IDs.append(int(pid[1:]))
                    file_participant_names.append(pid)
                    urls.append(os.path.join(*url.split(os.sep)[-2:]))

            # Participant 1, marked in tiers with "i1", is the participant with the highest ID.
            # Participant 2 (i2), is the one with the lowest ID.
            self._participants = {
                'i1': ParticipantURL('i1',
                                     file_participant_names[np.argmax(file_participant_IDs)],
                                     urls[np.argmax(file_participant_IDs)]),
                'i2': ParticipantURL('i2',
                                     file_participant_names[np.argmin(file_participant_IDs)],
                                     urls[np.argmin(file_participant_IDs)])
            }
        return self._participants

    def collect_islr_samples(self, participant_ID: str, start_ID: int) -> [ISLRSample]:
        """Parse the samples for a given participant.
        We collect all right hand glosses.

        :param participant_ID: Only collect annotations for this participant.
        :param start_ID: We will begin with this ID.
        :return: A list of samples."""
        participant_name = self.participant_ids()[participant_ID].participant_name
        gloss_rh_tier = f'GlosRH {participant_ID}'

        samples = []

        try:
            for gloss_annotation in self._eaf.get_annotation_data_for_tier(gloss_rh_tier):
                if gloss_annotation[0] >= gloss_annotation[1]:  # start >= end: invalid.
                    continue
                sample = ISLRSample(start_ID,
                                    GlossAnnotation(gloss_annotation[2], gloss_annotation[0], gloss_annotation[1]),
                                    Metadata(str(self._eaf_path), participant_name, participant_ID),
                                    Videos(str(self._participants[participant_ID].uri),
                                           f'{os.path.basename(self._eaf_path)}_{start_ID}.mp4'))
                samples.append(sample)
                start_ID += 1
        except KeyError:  # GlosRH tier not found.
            pass

        return samples
