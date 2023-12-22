"""Perform human pose estimation using MediaPipe Holistic."""
import argparse
import os

import cv2
import mediapipe as mp
import numpy as np

mp_holistic = mp.solutions.holistic


def run_mediapipe(video_path: str) -> np.ndarray:
    """Perform human pose estimation using MediaPipe Holistic for a given video.
    The video will be processed in its entirety, and a NumPy array will be returned containing the pose keypoints.

    The shape of the NumPy array is (L, 75, 3), where L is the number of video frames,
    75 is the number of extracted keypoints, and 3 is the coordinate dimensionality (x, y, z).
    If a keypoint was not detected by MediaPipe, it will be set to `np.nan`.

    The order of the keypoints is always:
        - body pose (33)
        - left hand (21)
        - right hand (21)

    :param video_path: Path to the video file.
    :returns: A NumPy array of shape (L, 75, 3) containing the keypoints.
    :raises FileNotFoundError: If the video file was not found."""

    # Processing of the video.
    with mp_holistic.Holistic(
            static_image_mode=False,
            model_complexity=2,
            smooth_landmarks=True,
            min_tracking_confidence=0.75) as holistic:
        frames = []

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise FileNotFoundError(
                f'Could not open the video clip with path `{video_path}`. '
                f'Please check whether you have provided the correct filename.')
        while cap.isOpened():
            success, frame = cap.read()
            if not success:  # Reached the end of the file.
                break
            frame_landmarks = holistic.process(frame)

            frame_output = []

            if frame_landmarks.pose_landmarks:
                landmarks = np.stack([np.array([l.x, l.y, l.z]) for l in frame_landmarks.pose_landmarks.landmark])
                frame_output.append(landmarks)
            else:
                frame_output.append(np.full((33, 3), np.nan))
            if frame_landmarks.left_hand_landmarks:
                landmarks = np.stack(
                    [np.array([l.x, l.y, l.z]) for l in frame_landmarks.left_hand_landmarks.landmark])
                frame_output.append(landmarks)
            else:
                frame_output.append(np.full((21, 3), np.nan))
            if frame_landmarks.right_hand_landmarks:
                landmarks = np.stack(
                    [np.array([l.x, l.y, l.z]) for l in frame_landmarks.right_hand_landmarks.landmark])
                frame_output.append(landmarks)
            else:
                frame_output.append(np.full((21, 3), np.nan))

            frames.append(np.concatenate(frame_output, axis=0))
        cap.release()

        return np.stack(frames)


def main(args):
    output_path = os.path.join(args.out_dir, os.path.basename(args.clip).replace('.mp4', '.npy'))
    if not os.path.isfile(output_path):
        keypoints = run_mediapipe(args.clip)
        np.save(output_path, keypoints)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--clip', type=str,
                        help='Path to the video from which we will extract MediaPipe features.')
    parser.add_argument('--out_dir', type=str, help='Output directory to which MediaPipe features will be saved.')

    args = parser.parse_args()

    main(args)