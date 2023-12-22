These are the steps/python scripts that allow for the extraction of an ISLR dataset for the BSLCP corpus. 

NB: There were some errors present in the EAF annotation files which had to be manually edited. 
Before proceeding, ammend G17n.eaf line 4 to include the correct videopath (i.e. "...Narratives/Compressed/G17n-comp.mov")

1. Parsing ELAN
    - run parse_elan.py: Parses all ELAN files and creates a JSON file and a CSV file of results. 
        Arguments:
            --eaf_root: The directory in which .eaf files are stored
            --json_out: Desired output/path/to/file.json
            --csv_out: Desired output/path/to/file.csv
        Optional argument:
            --all: To parse all tiers of annotation (including full translation) into single JSON file.

2. Cleaning
    - run clean_dataset.py: Removes fingerspelling, signs appearing fewer than 3 times, signs annotators were not sure of and ammends misaligned timestamps.
        Arguments:
            --csv_in: Path to .csv output of parse_elan.py
            --offset_file: Path to offset.json which ammends timestamp offsets.**
            --csv_out: Desired output/path/to/file.csv
    
3. Create and split dataset
    - run create_dataset.py: Performs a stratified split of the data and encodes interger labels. 
        Arguments: 
            --csv_in: Path to .csv output of clean_dataset.py
            --csv_out: Desired output/path/to/file.csv

4. Extract clips
    - run extract_clips.py: Extracts single sign clips from original videos and produces final samples.csv 
        Arguments: 
            --data_dir: Path to directory containing original videos.
            --csv_in: Path to .csv output of create_dataset.py.
            --out_dir: Desired output path for resulting clips.
            --csv_out: Desired output/path/to/file.csv.

5. Extract pose data
    - run pose_estimation.py: Extracts pose estimation keypoints from clips resulting from extract_clips.py.
        Arguments:
            --clip: Path to clip we want to extract keypoints from.
            --out_dir: Destired output path for resulting .npy file. 


** These timestamps have been ammeded manually to cope with with misaligned timestamps to the best of our ability. 
This is by no means a perfect solution but there was an improvement after this process. 
