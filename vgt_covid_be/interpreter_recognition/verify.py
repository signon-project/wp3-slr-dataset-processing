"""Tool to play segments using OpenCV, to verify them.
"""
import argparse
import json
import os

import cv2


def main(args):
    with open(args.annotation_file) as af:
        annotations = json.loads(af.read())
        segments = annotations['signing_times']

        cap = cv2.VideoCapture(args.input_sample)
        fps = cap.get(cv2.CAP_PROP_FPS)

        for segment in segments:
            current_frame_index = segment['start'] * fps
            cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame_index)

            while cap.isOpened():
                success, image = cap.read()
                if not success:
                    print(f'Unable to read frame from stream {os.path.basename(args.input_sample)}')
                    break

                if current_frame_index >= segment['end'] * fps:
                    # Time to go to the next segment.
                    break

                cv2.imshow('Frame', image)
                # Break when we press Q.
                # We wait for 16 ms between frames to go through the video as quickly as possible.
                if cv2.waitKey(16) & 0xFF == ord('q'):
                    break

                # Skip ahead by 2 seconds.
                current_frame_index += 2 * fps
                cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame_index)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('-i', '--input-sample', help='Path to the MP4 file to process.', type=str, required=True)
    parser.add_argument('-a', '--annotation-file', help='The annotation file from which to get segments', type=str,
                        required=True)
    args = parser.parse_args()

    main(args)
