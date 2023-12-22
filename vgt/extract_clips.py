"""Extract shorter clips from the source videos, ready for ML model training."""
import argparse
import csv
import os
import subprocess


def main(args):
    # Create gloss label encoding from gloss file.
    gloss_to_index = dict()
    with open(args.gloss_csv) as gloss_file:
        reader = csv.reader(gloss_file)
        # Gloss,Count
        _header = next(reader)
        for i, row in enumerate(reader):
            gloss_to_index[row[0]] = i

    output_samples = []
    with open(args.dataset_csv) as dataset_file:
        reader = csv.reader(dataset_file)
        # Id,Gloss,start_ms,end_ms,Participant,SourceVideo,SampleVideo,subset
        _header = next(reader)
        for row in reader:
            sample_id, gloss, start_ms, end_ms, participant, source_video, output_video, subset = row

            gloss_encoding = gloss_to_index[gloss]
            output_samples.append([sample_id, gloss_encoding, participant, output_video, subset])

            extract_subclip(os.path.join(args.video_dir, source_video), start_ms, end_ms,
                            os.path.join(args.out_dir, output_video))

    with open(args.out_csv, 'w') as output_csv_file:
        writer = csv.writer(output_csv_file)
        writer.writerow(['Id', 'Label', 'Participant', 'Video', 'Subset'])
        for sample in output_samples:
            writer.writerow(sample)


def extract_subclip(source_video: str, start_ms: int, end_ms: int, output_video: str):
    """Extract a subclip from `start_ms` to `end_ms` from `source_video`, and write it to `output_video`."""
    if os.path.isfile(output_video):
        return
    subprocess.run(["ffmpeg", "-i", source_video, "-ss", f"{start_ms}ms", "-to", f"{end_ms}ms", "-filter:v", "fps=25",
                    output_video])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('dataset_csv', type=str, help='CSV file containing sample information (from split_dataset.py).')
    parser.add_argument('gloss_csv', type=str, help='CSV file containing gloss counts (from create_dataset.py).')
    parser.add_argument('video_dir', type=str, help='Root video directory.')
    parser.add_argument('out_dir', type=str, help='Output directory for videos.')
    parser.add_argument('out_csv', type=str, help='CSV output containing dataset information ready for ML training.')

    args = parser.parse_args()

    main(args)
