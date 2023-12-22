"""Collect metadata useful for the application of the classifier.

We get the bounding box by visualizing frames using OpenCV and when we click, on the (x, y) position,
we get the cursor location.
"""
import argparse
import json
import os
import sys

import cv2


def get_click_callback(output_dict):
    def click_callback(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONUP:
            print('x = %d, y = %d' % (x, y))
            output_dict['x'] = x
            output_dict['y'] = y

    return click_callback


def main(args):
    bounding_box = {}

    with open(args.metadata) as metafile:
        metadata = json.loads(metafile.read())
        start_seconds = metadata['start']

    cv2.namedWindow('Frame')
    cv2.setMouseCallback('Frame', get_click_callback(bounding_box))

    cap = cv2.VideoCapture(args.input_sample)
    fps = cap.get(cv2.CAP_PROP_FPS)
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_seconds * fps)

    while cap.isOpened():
        success, image = cap.read()
        if not success:
            print(f'Unable to read frame from stream {os.path.basename(args.input_sample)}')
            break

        cv2.imshow('Frame', image)
        cv2.waitKey(0)

        if 'x' in bounding_box:
            # Found position. Print and exit.
            bounding_box['width'] = image.shape[1] - bounding_box['x']
            bounding_box['height'] = image.shape[0] - bounding_box['y']

            with open(args.metadata, 'w') as metafile:
                metadata['bounding_box'] = bounding_box
                metafile.write(json.dumps(metadata, indent=4))

            sys.exit(0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('-i', '--input-sample', help='Path to the MP4 file to process.', type=str, required=True)
    parser.add_argument('-m', '--metadata', help='Path to the input and output metadata file.', type=str, required=True)
    args = parser.parse_args()

    main(args)
