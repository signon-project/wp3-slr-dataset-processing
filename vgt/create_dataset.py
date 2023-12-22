import argparse
import csv
import dataclasses
import os
import re
from collections import Counter

from elan_parser import find_eaf_files, VGTEaf

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('eaf_root', type=str, help='Root directory of the VGT corpus .eaf files.')
    parser.add_argument('video_root', type=str, help='Root directory of the VGT corpus video files.')
    parser.add_argument('out_csv', type=str, help='Output CSV file.')
    parser.add_argument('glosses_csv', type=str, help='Output CSV file for gloss counter')

    args = parser.parse_args()

    # 1. Collect EAF files.
    eaf_filepaths = find_eaf_files(args.eaf_root)
    eaf_files = list(filter(lambda f: f.is_valid(), [VGTEaf(fp, args.video_root) for fp in eaf_filepaths]))

    # 2. Collect gloss annotations from all files.
    id = 0
    samples = []
    for eaf_file in eaf_files:
        annots = eaf_file.collect_islr_samples('i1', id)
        if len(annots) > 0:
            id = annots[-1].id + 1
            samples.extend(annots)
        annots = eaf_file.collect_islr_samples('i2', id)
        if len(annots) > 0:
            id = annots[-1].id + 1
            samples.extend(annots)


    # 3. Pre-process the glosses in the samples.
    def _to_upper(match_obj):
        char_elem = match_obj.group(0)
        return char_elem.upper()


    def _split_fingerspelling(match_obj):
        return 'VS:_' + ' VS:_'.join(list(match_obj.group(1)))


    regex_map = [
        # List of tuples instead of dictionary, to preserve order. (Could also have used OrderedDict).
        # Lowercase to uppercase.
        (re.compile(r'^(.*)$'), _to_upper),
        # Question marks.
        (re.compile(r'^\?+$'), r'<UNK>'),
        (re.compile(r'^([^\?]*)\?+$'), r'\1'),
        (re.compile(r'^\?+([^\?]*)$'), r'\1'),
        # Asymmetrical signs.
        (re.compile(r'\([aA][cC]\)'), r''),
        # Location markings.
        (re.compile(r'\(?[lL][oO][cC]:[^\)]*\)?'), r''),
        # False starts and mistakes.
        (re.compile(r'[§\*]$'), r''),
        # Colons.
        (re.compile(r':'), r'_'),
        # Repetitions.
        (re.compile(r'\++$'), r''),
        # Buoys.
        (re.compile(r'^.*lijstboei.*$'), r'<UNK>'),
        # Pointing signs.
        (re.compile(r'(WG-\d)_?.+'), r'\1'),
        # Quotation marks.
        (re.compile(r'"'), r''),
        (re.compile(r"'"), r''),
        # Underscores.
        (re.compile(r'_+'), r'_'),
        (re.compile(r'_$'), r''),
        (re.compile(r'^_'), r'')
    ]

    unique_glosses = len(set([s.gloss.gloss for s in samples]))
    print(f'Before normalizing the glosses, there are {unique_glosses} unique glosses in {len(samples)} samples.')
    for sample in samples:
        for pattern, replacement in regex_map:
            sample.gloss.gloss = re.sub(pattern, replacement, sample.gloss.gloss)
    unique_glosses = len(set([s.gloss.gloss for s in samples]))
    print(f'After pre-processing the glosses, there are {unique_glosses} unique glosses in {len(samples)} samples.')


    def _gloss_filter(gloss):
        # We don't want the faulty annotations, and there is no point in trying to recognize name signs
        # that will most likely not occur in the use cases of this tool anyway.
        # Let's also ignore fingerspelling and keep that for a separate fingerspelling recognizer.
        # We also ignore sign constructions (part of productive lexicon).
        unwanted_gloss = gloss == '<UNK>' or gloss.startswith('NG_') or gloss.startswith('G_') or gloss.startswith(
            'GC_') or gloss == 'G' or gloss.startswith('VS_')
        return not unwanted_gloss


    unique_glosses = len(set([s.gloss.gloss for s in samples]))
    print(f'Before filtering the glosses, there are {unique_glosses} unique glosses in {len(samples)} samples.')
    samples = list(filter(lambda s: _gloss_filter(s.gloss.gloss), samples))
    unique_glosses = len(set([s.gloss.gloss for s in samples]))
    print(f'After filtering the glosses, there are {unique_glosses} unique glosses in {len(samples)} samples.')

    # 4. Count the number of occurrences of each gloss.
    gloss_counter = Counter([s.gloss.gloss for s in samples])

    # Keep only those samples which have a gloss that occurs at least 20 times.
    # At the time of writing this comment, this resulted in 28,701 samples.
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
            ['Id', 'Gloss', 'start_ms', 'end_ms', 'EAF', 'Participant', 'Signer', 'SourceVideo', 'SampleVideo'])
        for sample in samples:
            writer.writerow(list(_flatten(dataclasses.astuple(sample))))

    with open(args.glosses_csv, 'w') as of:
        writer = csv.writer(of)
        writer.writerow(['Gloss', 'Count'])
        for gloss, count in gloss_counter.most_common(unique_glosses):
            writer.writerow([gloss, count])
