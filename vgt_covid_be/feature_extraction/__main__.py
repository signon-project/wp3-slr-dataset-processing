import argparse
import glob
import os

import numpy as np

import feature_extraction.extract_mediapipe as mediapipe

# The modules corresponding to the names of the features passed to this script's `f` flag.
# We could also use importlib but this is easier.
FEATURE_MODULES = {
    'mediapipe': mediapipe
}


def main(args):
    clip_path = os.path.join(args.directory, args.pattern)
    print(f'Looking for clips in {clip_path}')
    clips = glob.glob(clip_path)
    print(clips)
    for clip in clips:
        clip_features = {}

        feature_types = args.features.split(',')
        for feature_type in feature_types:
            module = FEATURE_MODULES[feature_type]
            clip_features[feature_type] = module.extract(clip)

        for feature_type in clip_features.keys():
            output_dir = os.path.join(args.output, feature_type)
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, os.path.basename(clip).replace('.mp4', '.npy'))
            np.save(output_path, clip_features[feature_type])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('-d', '--directory', help='The input directory containing the clips', type=str, required=True)
    parser.add_argument('-p', '--pattern', help='The file matching pattern', type=str, default='*VGT*.mp4')
    parser.add_argument('-f', '--features', help='Which features to extract, as a comma separated list.', type=str,
                        default='mediapipe')
    parser.add_argument('-o', '--output', help='The output directory to which the extracted features will be saved',
                        type=str, required=True)

    args = parser.parse_args()

    main(args)
