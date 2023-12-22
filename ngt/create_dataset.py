import argparse
import csv
import dataclasses
import os
from collections import Counter

import cv2

from elan_parser import find_eaf_files, NGTEaf, ISLRSample

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('eaf_root', type=str, help='Root directory of the NGT corpus .eaf files.')
    parser.add_argument('video_root', type=str, help='Root directory of the NGT corpus video files.')
    parser.add_argument('out_csv', type=str, help='Output CSV file.')
    parser.add_argument('glosses_csv', type=str, help='Output CSV file for gloss counter')

    args = parser.parse_args()

    # 1. Collect EAF files.
    eaf_filepaths = find_eaf_files(args.eaf_root)
    eaf_files = list(filter(lambda f: f.is_valid(), [NGTEaf(fp, args.video_root) for fp in eaf_filepaths]))

    # 2. Collect gloss annotations from all files.
    id = 0
    samples = []
    for eaf_file in eaf_files:
        annots = eaf_file.collect_islr_samples('S1', id)
        if len(annots) > 0:
            id = annots[-1].id + 1
            samples.extend(annots)
        annots = eaf_file.collect_islr_samples('S2', id)
        if len(annots) > 0:
            id = annots[-1].id + 1
            samples.extend(annots)


    # For the NGT corpus, there are some annotations that are outside the effective video duration.
    # We detect and remove those...
    # We first extract the durations for every video, caching them, to avoid superfluous calculations.

    def _get_video_duration(filename):
        video = cv2.VideoCapture(filename)
        # duration = video.get(cv2.CAP_PROP_POS_MSEC)  # Bugged...
        frame_count = video.get(cv2.CAP_PROP_FRAME_COUNT)
        fps = video.get(cv2.CAP_PROP_FPS)
        return int(1000 * frame_count / fps)


    duration_cache = dict()
    for sample in samples:
        video_url = os.path.join(args.video_root, sample.videos.source_video.split('_')[0] + '.mpg')
        if video_url not in duration_cache:
            duration_cache[video_url] = _get_video_duration(video_url)


    def _annotation_time_valid(sample: ISLRSample) -> bool:
        video_url = os.path.join(args.video_root, sample.videos.source_video.split('_')[0] + '.mpg')
        start_ms = sample.gloss.start_ms
        end_ms = sample.gloss.end_ms
        duration_ms = duration_cache[video_url]
        retval = start_ms < duration_ms and end_ms < duration_ms
        return retval


    samples = list(filter(_annotation_time_valid, samples))


    def _gloss_filter(gloss):
        # We don't want the faulty annotations, and we don't want annotations that the annotator was unsure about.
        # Let's also drop fingerspelling for now, a separate fingerspelling classifier should be trained for this.
        unwanted_gloss = gloss.startswith('?') or gloss.startswith('~') or gloss.startswith(
            '#') or gloss == '' or gloss == 'imitatie' or gloss == '!' or gloss.startswith('MOVE') or gloss.startswith(
            'PT:') or gloss.startswith('SHAPE')
        return not unwanted_gloss


    unique_glosses = len(set([s.gloss.gloss for s in samples]))
    print(f'Before filtering the glosses, there are {unique_glosses} unique glosses in {len(samples)} samples.')
    samples = list(filter(lambda s: _gloss_filter(s.gloss.gloss), samples))
    unique_glosses = len(set([s.gloss.gloss for s in samples]))
    print(f'After filtering the glosses, there are {unique_glosses} unique glosses in {len(samples)} samples.')

    # 4. Count the number of occurrences of each gloss.
    gloss_counter = Counter([s.gloss.gloss for s in samples])

    # Keep only those samples which have a gloss that occurs at least 20 times.
    # At the time of writing this comment, this resulted in 73980 samples.
    unique_glosses = len(set([s.gloss.gloss for s in samples]))
    print(f'Before reducing the samples, there are {unique_glosses} unique glosses in {len(samples)} samples.')
    samples = list(filter(lambda s: s.gloss.gloss in [e[0] for e in gloss_counter.items() if e[1] >= 20], samples))
    unique_glosses = len(set([s.gloss.gloss for s in samples]))
    print(f'After reducing the samples, there are {unique_glosses} unique glosses in {len(samples)} samples.')

    # 5. Reduce the EAF path to a relative path.
    for sample in samples:
        sample.metadata.filename = os.path.join(*sample.metadata.filename.split(os.sep)[-2:])


    # 6. Save CSV files.
    # Flatten tuples.
    def _flatten(data):
        if isinstance(data, tuple):
            for x in data:
                yield from _flatten(x)
        else:
            yield data


    with open(args.out_csv, 'w') as of:
        writer = csv.writer(of)
        writer.writerow(
            ['Id', 'Gloss', 'start_ms', 'end_ms', 'EAF', 'Participant', 'Signer', 'Side', 'SourceVideo', 'SampleVideo'])
        for sample in samples:
            writer.writerow(list(_flatten(dataclasses.astuple(sample))))

    with open(args.glosses_csv, 'w') as of:
        writer = csv.writer(of)
        writer.writerow(['Gloss', 'Count'])
        for gloss, count in gloss_counter.most_common(unique_glosses):
            writer.writerow([gloss, count])
