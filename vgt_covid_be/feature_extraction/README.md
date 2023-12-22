# Sign Language Recognition: Feature extraction

This repository contains code and documentation for sign language recognition.
In particular, the feature extraction process itself is handled in this repository.

## Feature extraction

The feature extraction is performed in an off-line fashion, i.e., the feature extractor is not trained end-to-end with the translation model.

Because of this, a powerful feature extractor is needed.

The currently available feature extractors are:

- MediaPipe Holistic (3D pose estimation) [CPU based]

### Requirements

Below are the software requirements for running feature extraction.
You can also see the full requirements in `feature_extraction/requirements.txt`.
We recommend making a virtual environment.

- Python 3.8
- NumPy
- MediaPipe

### Usage

Run `python3 -m feature_extraction -d PATH_TO_CLIPS/ -o OUTPUT_DIR/ -p PATTERN -f FEATURES`.

#### Flags

- `-d`: The path to the directory containing the clips for which you wish to perform feature extraction.
- `-o`: The path to the directory to which the feature files will be written. The files will be named the same as the clips, but with the `.npy` extension.
- `-p`: The file pattern to match. For example, if your video files are named "something\_VGT.mp4", you will want to use `*_VGT.mp4` as pattern to skip other files
in the given directory.
- `-f`: The features you wish to extract as a comma separated list. Valid keys are:
	- `mediapipe` for MediaPipe Holistic

#### Example

```
python3 -m feature_extraction -d /data/videos/covid_clips \
	-o /data/features/mediapipe \
	-p *_VGT.mp4
	-f mediapipe
```

## Post-processing

Some of the feature extractors require or benefit from post-processing.
For example, in the case of MediaPipe Holistic, it makes sense to drop some of the 543 landmarks.

No post-processing modules are currently available.
