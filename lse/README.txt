These scripts allow for the extraction of an ISLR dataset from the LSE signhub data.

There are a couple of top level scripts, which are intended to be run in a certain order.

1. create_dataset.py: Parses all ELAN files and creates two CSV files:
    - dataset file: Containing all instances of isolated signs.
    - glosses file: Containing the glosses and their counts in the dataset.
2. split_dataset.py: Creates a stratified grouped split (train/validate/test) from the dataset file. Writes a new file.
3. extract_clips.py: Extracts from the full videos the subclips that correspond to individual samples. Writes a new
    file that can be used directly in an ML model.
4. pose_estimation.py: Extracts body pose and hand pose keypoints from the clips resulting from extract_clips.py. These
    features are saved in NumPy arrays (one array per video). The raw coordinates are saved, and NaN values indicate
    missing keypoints.
    - Recommended usage: run in parallel using GNU Parallel and the command `find clips -name "*.mp4" | parallel -I% --max-args 1 --jobs 4 python3 pose_estimation.py % mediapipe`

