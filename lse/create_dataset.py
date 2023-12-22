import argparse
import csv
import dataclasses
import os
import re
from collections import Counter

from elan_parser import find_eaf_files, LSEEaf

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('eaf_root', type=str, help='Root directory of the VGT corpus .eaf files.')
    parser.add_argument('video_root', type=str, help='Root directory of the VGT corpus video files.')
    parser.add_argument('out_csv', type=str, help='Output CSV file.')
    parser.add_argument('glosses_csv', type=str, help='Output CSV file for gloss counter')

    args = parser.parse_args()

    # 1. Collect EAF files.
    eaf_filepaths = find_eaf_files(args.eaf_root)
    eaf_files = [LSEEaf(fp, args.video_root) for fp in eaf_filepaths]

    # 2. Collect gloss annotations from all files.
    id = 0
    samples = []
    for eaf_file in eaf_files:
        annots = eaf_file.collect_islr_samples(id)
        if len(annots) > 0:
            id = annots[-1].id + 1
            samples.extend(annots)


    # 3. Pre-process the glosses in the samples.
    def _to_upper(match_obj):
        char_elem = match_obj.group(0)
        return char_elem.upper()

    unique_glosses = len(set([s.gloss.gloss for s in samples]))
    print(f'After pre-processing the glosses, there are {unique_glosses} unique glosses in {len(samples)} samples.')


    # 4. Count the number of occurrences of each gloss.
    gloss_counter = Counter([s.gloss.gloss for s in samples])

    # Keep only those samples which have a gloss that occurs at least 5 times.
    # At the time of writing this comment, this resulted in 2,535 samples.
    unique_glosses = len(set([s.gloss.gloss for s in samples]))
    print(f'Before reducing the samples, there are {unique_glosses} unique glosses in {len(samples)} samples.')
    samples = list(filter(lambda s: s.gloss.gloss in [e[0] for e in gloss_counter.items() if e[1] >= 5], samples))
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
            ['Id', 'Gloss', 'start_ms', 'end_ms', 'EAF', 'Participant', 'SourceVideo', 'SampleVideo'])
        for sample in samples:
            writer.writerow(list(_flatten(dataclasses.astuple(sample))))

    with open(args.glosses_csv, 'w') as of:
        writer = csv.writer(of)
        writer.writerow(['Gloss', 'Count'])
        for gloss, count in gloss_counter.most_common(unique_glosses):
            writer.writerow([gloss, count])
