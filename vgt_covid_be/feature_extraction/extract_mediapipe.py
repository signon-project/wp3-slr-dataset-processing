"""Extract features using MediaPipe Holistic (https://google.github.io/mediapipe/solutions/holistic.html).
We extract all landmarks (if they are found) per frame.
It is possible that for certain frames, the landmarks of certain body parts are missing.
In that case, for that frame and that body part, this module will yield `None`."""

import cv2
import numpy as np
import mediapipe as mp

mp_holistic = mp.solutions.holistic


def extract(filename):
    """Extract all MediaPipe holistic landmarks from the given video.

    :param filename: Path to the video.
    :returns: A dictionary, containing the keys "pose", "left_hand", "right_hand" and "face".
      Each element in the dictionary is a list of either an array or None, if the body part was not detected
      for a given frame. There are as many elements in the list as there are frames in the clip.
    """
    with mp_holistic.Holistic(
            static_image_mode=False,
            model_complexity=2,
            smooth_landmarks=True,
            min_tracking_confidence=0.75) as holistic:
        results = {
            "pose": [],
            "left_hand": [],
            "right_hand": [],
            "face": [],
        }

        cap = cv2.VideoCapture(filename)
        if not cap.isOpened():
            raise ValueError(
                f'Could not open the video clip with path `{filename}`. '
                f'Please check whether you have provided the correct filename.')
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                break
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_landmarks = holistic.process(frame)

            _append_landmarks(frame_landmarks.pose_landmarks, results, "pose")
            _append_landmarks(frame_landmarks.face_landmarks, results, "face")
            _append_landmarks(frame_landmarks.left_hand_landmarks, results, "left_hand")
            _append_landmarks(frame_landmarks.right_hand_landmarks, results, "right_hand")
        cap.release()
        return results


def _append_landmarks(body_landmarks, results, key):
    """Helper function which appends the raw coordinates.

    :param body_landmarks: The landmarks list as provided by MediaPipe Holistic.
    :param results: The dictionary to which to write the landmarks.
    :param key: The key to index the dictionary with."""
    if body_landmarks:
        landmarks = np.stack([np.array([l.x, l.y, l.z]) for l in body_landmarks.landmark])
        results[key].append(landmarks)
    else:
        results[key].append(None)
