import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from pympi import Eaf


def find_eaf_files(root_dir: str) -> [str]:
    """Collect all ELAN files for the NGT corpus.
    Hidden files are ignored.

    :param root_dir: The root directory under which the ELAN files are located.
    :return: A list of absolute paths to the ELAN files."""
    return sorted(filter(lambda p: not os.path.basename(p).startswith('.'), Path(root_dir).rglob('*.eaf')))


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
    side: str  # The side of the video to cut out (left half or right half)
    source_video: str
    sample_video: str


@dataclass
class ISLRSample:
    id: int
    gloss: GlossAnnotation
    metadata: Metadata
    videos: Videos


class NGTEaf:
    """Contains all the relevant information for the NGT corpus present in .eaf files."""

    def __init__(self, eaf_path: str, video_root: str):
        """Create a new NGTEaf instance.

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
        """Certain files in the NGT Corpus are invalid. These are files that contain media URLs that are
        inaccessible, e.g., on the annotator's local machine."""
        media = self._eaf.media_descriptors
        urls = [e['MEDIA_URL'] for e in media]
        if len(urls) < 2:
            return False
        urls = list(filter(lambda u: u.endswith('_b.mpg'), urls))
        if len(urls) < 2:
            return False
        ok = False
        for url in urls:
            # Only keep those files that are linked to the videos we have.
            full_path = os.path.join(self._video_root, os.path.basename(url))
            # Drop _Sxyz_b.mpg -> last 11 characters.
            full_path = full_path[:-11] + '.mpg'
            ok = os.path.isfile(full_path)
        if not ok:
            return False
        try:
            gloss_rh_tiers = ['GlossR S1', 'GlossR S2']
            for tier in gloss_rh_tiers:
                participant_name = self._eaf.get_parameters_for_tier(tier)['PARTICIPANT']
                ok = ok and self._get_participant_url(participant_name) is not None
            return ok
        except KeyError:
            return False

    def _get_participant_url(self, participant_name) -> Optional[str]:
        """Get the URL for a given participant name."""
        media = self._eaf.media_descriptors
        for entry in media:
            url = entry['MEDIA_URL']
            if not url.endswith('_b.mpg'):
                continue
            basename = os.path.basename(url)
            pid = basename.split('_')[-2]
            if pid == participant_name:
                return basename
        return None

    def collect_islr_samples(self, participant_ID: str, start_ID: int) -> [ISLRSample]:
        """Parse the samples for a given participant.
        We collect all right hand glosses.

        :param participant_ID: Only collect annotations for this participant.
        :param start_ID: We will begin with this ID.
        :return: A list of samples."""
        gloss_rh_tier = f'GlossR {participant_ID}'

        samples = []

        try:
            participant_name = self._eaf.get_parameters_for_tier(gloss_rh_tier)['PARTICIPANT']
            url = self._get_participant_url(participant_name)
            side = 'left' if participant_ID == 'S1' else 'right'

            for gloss_annotation in self._eaf.get_annotation_data_for_tier(gloss_rh_tier):
                if gloss_annotation[0] >= gloss_annotation[1]:  # start >= end: invalid.
                    continue
                sample = ISLRSample(start_ID,
                                    GlossAnnotation(gloss_annotation[2], gloss_annotation[0], gloss_annotation[1]),
                                    Metadata(str(self._eaf_path), participant_name, participant_ID),
                                    Videos(side, str(url), f'{os.path.basename(self._eaf_path)}_{start_ID}.mp4'))
                samples.append(sample)
                start_ID += 1
        except KeyError:  # GlossR tier not found.
            pass

        return samples
