import argparse
import json
import os

import PIL
import cv2
import torch
from torchvision.transforms import transforms

from model import Classifier


def main(args):
    model = Classifier()
    model.load_state_dict(torch.load(args.checkpoint_path, map_location='cpu'), strict=True)
    model.eval()
    model.to(args.device)

    eval_transforms = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    bounding_box = [int(e) for e in args.bounding_box.split(',')]

    segments = []

    resolution = None

    with torch.no_grad():
        cap = cv2.VideoCapture(args.input_sample)
        fps = cap.get(cv2.CAP_PROP_FPS)

        tolerance_frames = args.tolerance * fps
        cur_diff_frames = 0
        previous_prediction = args.start_value == 'VGT'

        cap.set(cv2.CAP_PROP_POS_FRAMES, int(args.start_seconds * fps))
        current_frame_index = int(args.start_seconds * fps)
        while cap.isOpened():
            batch = []
            for _ in range(args.batch_size):
                success, image = cap.read()
                if not success:
                    print(f'Unable to read frame {current_frame_index} from stream {os.path.basename(args.input_sample)}')
                    break

                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                if resolution is None:
                    resolution = (image.shape[1], image.shape[0])
                image = image[bounding_box[1]:bounding_box[1] + bounding_box[3],
                        bounding_box[0]:bounding_box[0] + bounding_box[2]]
                frame = PIL.Image.fromarray(image)

                frame = eval_transforms(frame)
                batch.append(frame)

            if len(batch) == 0:
                break

            model_input = torch.stack(batch).to(args.device)

            model_output = model(model_input).cpu()
            model_predictions = model_output > 0.5

            for batch_idx in range(len(batch)):
                if len(batch) == 1:
                    model_prediction = model_predictions.item()
                else:
                    model_prediction = model_predictions[batch_idx].item()
                if model_prediction != previous_prediction:
                    cur_diff_frames += 1
                    if cur_diff_frames < tolerance_frames:
                        # Probably still the same, just a continuity error due to the frame based nature of the classifier
                        output_prediction = previous_prediction
                    else:
                        # Allowed to switch after the tolerance has been exceeded
                        cur_diff_frames = 0
                        output_prediction = model_prediction
                else:
                    cur_diff_frames = 0
                    output_prediction = model_prediction

                # Check if we need to start a new segment or end an existing one.
                current_segment = segments[-1] if len(segments) > 0 else None
                if not previous_prediction and output_prediction:
                    # We encountered a VGT frame, after an LSFB frame.
                    # Start new VGT segment.
                    # We don't know the end time yet.
                    segment = {
                        'start': int(current_frame_index // fps),
                        'end': -1,
                    }
                    segments.append(segment)
                elif not output_prediction and current_segment is not None and current_segment['end'] == -1:
                    # We encountered an LSFB frame, so if we already started a VGT segment, we need to end it.
                    assert previous_prediction, 'Encountered LSFB frame in an active VGT segment'
                    current_segment['end'] = int((current_frame_index - 1) // fps)

                previous_prediction = output_prediction
                current_frame_index += 1

            # (Removed) debug visualization
            # cv2.imshow(str(output_prediction), image)
            # cv2.waitKey(0)

        # If we ended the video in VGT mode, we need to set the last end index.
        if len(segments) > 0 and segments[-1]['end'] == -1:
            segments[-1]['end'] = current_frame_index - 1

        # Write the results.
        with open(args.output_file, 'w') as of:
            annotation = {
                'filename': os.path.basename(args.input_sample),
                'resolution': {
                    'width': resolution[0],
                    'height': resolution[1],
                    'fps': int(fps),
                },
                'signing_times': segments,
                'interpreter_bounding_box': {
                    'x': bounding_box[0],
                    'y': bounding_box[1],
                    'width': bounding_box[2],
                    'height': bounding_box[3]
                },
                'interpreter': args.interpreter
            }
            of.write(json.dumps(annotation, indent=4))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('-c', '--checkpoint-path', help='Path to the trained model checkpoint.', type=str,
                        required=True)
    parser.add_argument('-i', '--input-sample', help='Path to the MP4 file to process.', type=str, required=True)
    parser.add_argument('-s', '--start-seconds', help='Start at this number of seconds', type=int, required=True)
    parser.add_argument('-b', '--bounding-box', help='The bounding box as x,y,w,h', type=str, required=True)
    parser.add_argument('-t', '--tolerance', help='Tolerance of errors (seconds)', type=int, default=1)
    parser.add_argument('-a', '--start-value', help='The language of the initial frame', type=str, required=True)
    parser.add_argument('-o', '--output-file', help='Path to the output annotations file', type=str, required=True)
    parser.add_argument('-d', '--device', help='PyTorch device string', type=str, default='cpu')
    parser.add_argument('-z', '--batch-size', help='Batch size', type=int, default=1)
    parser.add_argument('-n', '--interpreter', help='Interpreter ID', type=int, required=True)

    args = parser.parse_args()

    main(args)
