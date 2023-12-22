# VGT COVID BE

This dataset contains press conferences during the COVID-19 pandemic in Belgium.
The Dutch spoken parts are interpreted by a native VGT signer, and the French spoken parts by a native LSFB signer. There are several signers per language.

## Dataset details

There are 212 MP4 videos of press conferences.
There are several VGT interpreters (currently identified: 3).

There are no sentence-level annotations. For part of the dataset, segment-level annotations are provided, indicating the segments of the videos where the VGT interpreter is actively signing on screen.

## Annotation process

The annotation format is JSON.
It stores the temporal location (start and end) of the sign language interpreter's appearance on screen as well as the spatial location
(a pixel space bounding box) of the interpreter. Per annotated source video file, such a JSON file is provided.

Here is an example.

```json
{
  "filename": "AND_20200320.mp4",
  "resolution": {
    "width": 1920,
    "height": 1080,
    "fps": 25
  },
  "signing_times": [
    {
      "start": 0.00,
      "end": 5123.44
    },
    {
      "start": 6013.33,
      "end": 10041.34
    }
  ],
  "interpreter_bounding_box": {
    "x": 1800,
    "y": 960,
    "width": 120,
    "height": 120
  },
  "signer": 1
}
```

In this format, we store metadata on the video, such as the spatial and temporal resolution. We also store the temporal
and spatial locations of the interpreter. The `start` and `end` annotations (seconds) are *inclusive*. The key `signer` is also present which has as value a signer ID. The individual signer
IDs are stored in the `interpreters/` folder, where a picture is used along with an ID to facilitate correct ID
assignment during data annotation.

The activity of the interpreter is not contained within this format. It purely indicates whether or not the interpreter
is present on screen. The actual detection of active signing is left to a next step in the pipeline.

### Creating annotation files

An initial set of files was manually annotated, after which a person classifier was trained to facilitate speeding up the annotation of the remainder of the videos. The details of this classifier are given in the `interpreter_recognition/` directory.

The classifier is applied in a frame based manner, using a sliding window to process entire clips. The predictions are post-processed using a filter to
reduce jitter in the predictions and ensure continuous clips. By applying the classifier in this way, we can automatically generate annotation files, which
are then easier to verify than to manually create.

### From annotation files to clips

The `extract_clips.py` script can be used to use the above annotation files to extract MP4 clips from the source videos.
It requests an input directory of annotation files and an output directory to write the MP4 clips to. It uses `ffmpeg` over `FTP` to extract the individual clips.

### From clips to features

Within the `feature_extraction/` directory, we can find code for the extraction of features for this dataset.

## Available feature sets

The following features are available for this dataset:

- MediaPipe Holistic

## Observations

Here are some observations made during annotation.

- Not all videos contain interpreters.
- The background is often different.
- The aspect ratio and resolution of the interpreter video is often different.
- There are several interpreters for VGT.
- The VGT and LSFB interpreters switch every few minutes (to interpret Belgian Dutch and French, respectively).
- In FOD_20200402.mp4, a sudden jump occurs at 35'51''. Likely, the sentences extracted from that part will be cut off.
- The videos have different frame rates, either 25 or 30, and different spatial resolutions ranging from 360p to 1080p.

## Citation

If you find this dataset or codebase helpful, please consider citing our work.

```
@article{vandeghinste2022becos,
  title={BeCoS Corpus: Belgian Covid-19 Sign Language Corpus. A Corpus for Training Sign Language Recognition and Translation},
  author={Vandeghinste, Vincent and Van Dyck, Bob and De Coster, Mathieu and Goddefroy, Maud and Dambre, Joni},
  journal={Computational Linguistics in the Netherlands Journal},
  volume={12},
  pages={7--17},
  year={2022}
}
```