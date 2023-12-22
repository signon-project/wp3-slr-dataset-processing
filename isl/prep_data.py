import os
import json
import numpy as np
import pandas as pd
import argparse

def gloss_dict_to_df(video_dict):
    '''Put gloss information into a dataframe.
    params: 
        video_dict(dict): Dictionary generated from ELAN containing the following fields (as per ISL Sounds 
        of Ireland Corpus):
        - relative_video_path 
        - annotations
            -> Lexical Gloss
        - fps
        
    returns:
        df (DataFrame) Dataframe containing the video name, the start and end time of the gloss, the gloss
        itself.
    '''
    video_name = video_dict["relative_video_path"].split('.')[0]
    fps = video_dict["fps"]
    if "Lexical Gloss" in video_dict["annotations"]:
        glosses = np.array(video_dict["annotations"]["Lexical Gloss"])
    else:
        glosses = np.array(video_dict["annotations"]["Lexical"])
    df = pd.DataFrame()
    df["video_name"] = [video_name]*len(glosses)
    df["fps"] = np.full(len(glosses), fps)
    df["start_ms"] = np.array(glosses[::,0])
    df["end_ms"] = np.array(glosses[::,1])
    df["gloss"] = np.array(glosses[::,2])
    df["start_ms"] = df["start_ms"].astype(float)
    df["end_ms"] = df["end_ms"].astype(float)
    return df

def get_correct_eafs(gloss):
    '''
    This function corrects duplicate EAF files that some videos have. 
    params: 
        gloss (dict): Gloss containing the contents of the EAF files as Json loaded dictionary. 
    returns:
        video_name_to_eaf_dict: 
        correct_eaf_files (list): Latest EAF file that is to be used.  
        discarded_eaf_files (dict): Duplicate EAF files to be discarded. 
    
    '''
    # Get the dictionary of EAF files that refer to a particular video. 
    # There should only be one, but there can be duplicates. 
    # The key is the video and the value is the list of EAF files that refer to this video. 
    all_video_name_to_eaf_dict = {}
    for eaf_file, video_dict in gloss.items():
        video_name = video_dict["relative_video_path"].split('.')[0]
        if video_name not in all_video_name_to_eaf_dict.keys():
            all_video_name_to_eaf_dict[video_name] = [eaf_file]
        else:
            all_video_name_to_eaf_dict[video_name].append(eaf_file)
    # Create a dictionary for the video->EAF file map with duplicates removed. 
    video_name_to_eaf_dict = {}
    # Dictionary that will keep track of discarded eaf files. 
    discarded_eaf_files = {}
    correct_eaf_files = []
    # Iterature over all the videos and EAF files. 
    for video_name, eaf_files in all_video_name_to_eaf_dict.items():
        # Check if there is more than 1 EAF file for that particular video. 
        if len(eaf_files) > 1: 
            for eaf_file in eaf_files:
                # There should only be one video source for each EAF file so if there
                # is already a video corresponding to that EAF file, we should choose the 
                # one with "final" and no "pfsx "in the name (based on the naming convension in the data)
                if ("final" in eaf_file.lower()) and ("pfsx" not in eaf_file.lower()):
                    final_eaf_file = eaf_file
                else:
                    discarded_eaf_files[eaf_file] = video_name
        else:
            # Otherwise there is only one eaf file corresponding to the video. 
            final_eaf_file = eaf_files[0]
        video_name_to_eaf_dict[video_name] = final_eaf_file       
        correct_eaf_files.append(final_eaf_file)
    return video_name_to_eaf_dict, correct_eaf_files, discarded_eaf_files

def get_frame_ms(df, FPS):
    '''
    Obtains the millisecond timestamp for a given frame and adds this as a column value to existing
    keypoints dataframe. 
    params: 
        df: DataFrame with keypoints. 
        FPS: Frames per second of videos. 
    returns: 
        df (DataFrame): Input DataFrame with the following additional fields: 
        - "video_file": The filename of a video (no path information).
        - "frame_ms": The millisecond timestamp at the frame. 
    '''
    df = df.reset_index()
    # Isolate frame number from jpg name
    df["frame_num"] = df["index"].str.split('_').apply(lambda x: x[-1])
    # Remove ".jpg" file extension
    df["frame_num"] = df.frame_num.str.split('.').apply(lambda x: x[0]).astype(int)
    df["video"] = df["index"].str.replace("_frame_\d.jpg", "", regex=True)
    df["frame_ms"] = (df.frame_num/FPS)*1000
    return df

def get_participant_name(glosses):
    personal_stories = [v for v in glosses.video_name.unique() if "Personal" in v]
    personal_stories_names = [' '.join(v.split('-')[2:]).split('(Converted)')[0] for v in personal_stories]
    personal_stories_map = dict(zip(personal_stories, personal_stories_names))

    frog_stories = [v for v in glosses.video_name.unique() if "Frog" in v]
    frog_stories_names = [' '.join(v.split('-')[:-1][1:]) for v in frog_stories]
    frog_stories_map = dict(zip(frog_stories, frog_stories_names))

    frog_stories_map_f = lambda x: frog_stories_map[x] if x in frog_stories_map.keys() else x
    personal_stories_map_f = lambda x: personal_stories_map[x] if x in personal_stories_map.keys() else x
    glosses["participant"] = glosses.video_name.apply(frog_stories_map_f)
    glosses["participant"] = glosses.participant.apply(personal_stories_map_f)
    return glosses

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

    #2. Remove glosses with fingerspelling which comes in the form: "w.o.r.d.":
    df = df[~df['gloss'].astype(str).str.contains('\.')]

    #3. Remove glosses where the annotator was unsure of the sign being performed.
    #   In this case the gloss with start with "?":
    df = df[~df['gloss'].astype(str).str.startswith('?')]

    return df

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--anno_json', type=str, help='Output .json file from parse_elan.py.')
    parser.add_argument('--csv_out', type=str, help='Desired path/to/output.csv.')
    parser.add_argument('--errors_out', type=str, help='Desired path/to/discarded_EAF_files.json.')

    args = parser.parse_args()

    #1. Load parsed annotations file:
    with open(args.anno_json, 'rb') as f:
        gloss = json.load(f)

    #2. Remove duplicate EAF files:
    video_name_to_eaf_dict, correct_eaf_files, discarded_eaf_files =  get_correct_eafs(gloss)  
    with open(args.errors_out, 'w') as f:
        json.dump(discarded_eaf_files, f)
    
    #3. Create csv file of filtered glosses
    #   Form: [video_name, fps, start_ms, end_ms, gloss, participant]
    gloss_dfs = [gloss_dict_to_df(gloss[eaf_file]) for eaf_file in correct_eaf_files]
    gloss_df= pd.concat(gloss_dfs)
    gloss_df = gloss_df.reset_index(drop=True)
    gloss_df = get_participant_name(gloss_df)
    gloss_df = _filter_gloss(gloss_df)

    #4.Save:
    gloss_df.to_csv(args.csv_out, index=False)