"""Feature extraction code for sign language translation.

This code extracts features from clips using pre-trained feature extractors.
There is a `main` module which performs the extraction, delegating to `extract_*` modules.
The `extract_*` modules must have a function `extract(filename)` which extracts the features of a single clip.
"""