import json
import argparse
import numpy as np
import pandas as pd


def _filter_gloss(df):
    """
    Filters out annotations which include fingerspelling, signs the annotators were unsure about and those that appear fewer than 3 times. 

    Parameters:
    -----------
    df: DataFrame
        Dataframe output of parse_elan.py, i.e. In form: video_name, start_ms, end_ms, gloss

    Returns:
    --------
    new_df: DataFrame
        Cleaned Dataframe in form: video_name, start_ms, end_ms, gloss. 
    """

    #1. Remove glosses that appear fewer than 3 times: 
    df = df[df.groupby('gloss').gloss.transform('count') >=3]

    #2. Remove glosses with fingerspelling tag "FS:":
    df = df[~df['gloss'].astype(str).str.contains('FS:')]

    #3. Remove glosses where the annotator was unsure of the sign being performed.
    #   In this case the gloss with start with "?" or end with "(UNKNOWN)" or is tagged as "INDECIPHERABLE:
    df = df[~df['gloss'].astype(str).str.endswith('(UNKNOWN)')]
    df = df[~df['gloss'].astype(str).str.startswith('?')]
    df = df[~df['gloss'].astype(str).str.contains('INDECIPHERABLE')]

    return df

def _fix_offset(df, offset):
    """
    Adjusts the timestamp offset based on the rough ms difference found in manual assessment. 
    NB: This was done to the best of our ability and is certainly not a perfect solution. We welcome 
    further work on this point. 

    Parameters:
    -----------
    df: DataFrame
        Dataframe (in form: video_name, start_ms, end_ms, gloss).
    
    offset: Dictionary
        Dictionary of timestamp ms offsets. 

    Returns:
    --------
    new_df: DataFrame
        Dataframe (in form: video_name, start_ms, end_ms, gloss) with adjusted timestamps.  
    """
    for key in offset:
        df.loc[df['video_name'] == key, ['start_ms', 'end_ms']] += offset[key]

    return df


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--csv_in', type=str, help='Path to CSV output of parse_elan.py')
    parser.add_argument('--offset_file', type=str, help='Path to offset.json file.')
    parser.add_argument('--csv_out', type=str, help='Output .csv file of cleaned dataset.')

    args = parser.parse_args()

    #1. Load CSV file from previous step:
    step1_df = pd.read_csv(args.csv_in)

    #2. Verify this is in the right form for cleaning/processing:
    #   Form: video_name, start_ms, end_ms, gloss
    col_names = list(step1_df)
    if not col_names == ['video_name', 'start_ms', 'end_ms', 'gloss']:
        raise Exception("CSV not in correct form. Check column values.")

    #3. Remove G16n.mov samples due issues with this video:
    _tmp = step1_df[step1_df.video_name != "G16n.mov"]
    
    #4. Filter out unwanted gloss values: 
    _tmp = _filter_gloss(_tmp)

    #5. Load JSON file with offset values and process:
    f = open(args.offset_file)
    offset = json.load(f)

    step2_df = _fix_offset(_tmp, offset)

    #6. Save:
    step2_df.to_csv(args.csv_out, index=False)

