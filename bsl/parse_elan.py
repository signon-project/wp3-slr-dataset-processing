import os
import glob
import json
import argparse
import numpy as np
import pandas as pd
from pympi.Elan import Eaf as eaf

def _elan_to_dict(annotation_filename, gloss_only=True):
    '''
    Converts an ELAN annotation file to a dictionary. 
    
    Parameters
    ----------
    annotation_filename : str
        Filename for specific annotation file. 
    gloss_only: boolean
        If True will parse only those EAF files that contain gloss level annotations
        If False will parse all EAF files
    
    Returns
    -------
    annotation_dict : dict
        Annotation dictionary taking the following form:
        {
             'relative_video_path': '...', 
             'video_format': '...', 
             'annotations': 
                {
                    'annotation tier 1': [(start_ms, end_ms, label), ..., start_ms, end_ms, label)], 
                    ...
                    'annotation tier k': [(start_ms, end_ms, label), ..., start_ms, end_ms, label)], 
        }
        where k are the number of tiers in the annotation. at and annotations. 
        
    '''
    annotation_eaf = eaf(annotation_filename)
    video_format = annotation_eaf.get_linked_files()[0]['MIME_TYPE']
    # This gets the video file path corresponding to the annotation file.
    # The whole path is not as useful, so we get the video file name and the enclosing directory. 
    # We could have used the "RELATIVE_URL" field but this does not exist for all files. 
    video_path = annotation_eaf.get_linked_files()[0]['MEDIA_URL'].split('/')[-1]

    # Get annotation tier names
    tier_names = list(annotation_eaf.get_tier_names())
    annotation_tier_dict = dict()

    # Only some EAF files include gloss level annotations
    # If gloss_only = True, we will extract data from only those EAFs which have gloss level annotations
    # Is set to False, we will extract all (i.e. just the 'Free Translation' tier)
    if not gloss_only:
        # Get annotation list from each tier of this EAF file and put it into a dictionary 
        for tier_name in annotation_eaf.get_tier_names():
            annotation_tier_dict[tier_name] = annotation_eaf.get_annotation_data_for_tier(tier_name)
        # Video file name is formatted like: 'BM23n-comp.mov' so need to remove the "-comp"
        video_name = video_path.split('-')[0]
        file_ext = video_path.split('.')[1]
        video_path = '.'.join([video_name, file_ext])
        
        # Return a dictionary with annotation information  
        return {"relative_video_path": video_path, 
                        "video_format": video_format,
                        "annotations": annotation_tier_dict
                        }

    else:
        # Here we want to return just the gloss level annotations
        if len(tier_names) > 1:
            # As there is overlap between LH and RH glosses, we will capture just the 'RH-IDgloss' tier and put it into a dictionary
            annotation_tier_dict['RH-IDgloss'] = annotation_eaf.get_annotation_data_for_tier('RH-IDgloss')
            # Video file name is formatted like: 'BM23n-comp.mov' so need to remove the "-comp"
            video_name = video_path.split('-')[0]
            file_ext = video_path.split('.')[1]
            video_path = '.'.join([video_name, file_ext])
            
            # Return a dictionary with gloss annotation information  
            return {"relative_video_path": video_path, 
                            "video_format": video_format,
                            "annotations": annotation_tier_dict
                            }

def gloss_dict_to_df(annotation_dict):
    '''
    Converts extracted gloss information into a Pandas DataFrame.
    params: 
        annotation_dict(dict): Dictionary generated from ELAN containing the following fields (as per BSL Corpus):
        - eaf_file:
            - relative_video_path 
            - video_format
            - annotations

    returns:
        df (DataFrame) Dataframe containing the following columns:
        - video_name
        - start_ms
        - end_ms
        - gloss
    '''
    dfs = []

    for v in annotation_dict.values():
        video_name = v['relative_video_path']
        video_glosses = v['annotations']

        df = pd.DataFrame()
        hand_glosses = np.array(video_glosses["RH-IDgloss"])
        df["video_name"] = [video_name]*len(hand_glosses)
        df["start_ms"] = hand_glosses[::,0]
        df["end_ms"] = hand_glosses[::,1]
        df["gloss"] = hand_glosses[::,2]
        df["start_ms"] = df["start_ms"].astype(float)
        df["end_ms"] = df["end_ms"].astype(float)

        dfs.append(df)

    out_df = pd.concat(dfs, ignore_index=True)
    
    return out_df

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--eaf_root', type=str, help='Root dir of the BSLCP corpus .eaf files.')
    parser.add_argument('--json_out', type=str, help='Output .json file of parsed results.')
    parser.add_argument('--csv_out', type=str, help='Output .csv file of parsed gloss results.')
    parser.add_argument('--all_json', action='store_true', help='Optional: To parse all tiers of annotation into JSON format.')

    args = parser.parse_args()

    # 1. Collect all EAF files:
    eaf_files = glob.glob(os.path.join(args.eaf_root, '*.eaf'))

    # 2. Process:
    if not args.all_json:
        # Just gloss level annotations:
        annotations = dict()
        for eaf_file in eaf_files:
            ann = _elan_to_dict(eaf_file)
            if ann is not None:
                annotations[eaf_file] = ann
        dataframe = gloss_dict_to_df(annotations)
        dataframe.to_csv(args.csv_out, index=False)
    else:
        # All tiers of annotations:
        annotations = dict()
        for eaf_file in eaf_files:
            ann = _elan_to_dict(eaf_file, False)
            annotations[eaf_file] = ann

    # 3. Save annotation dictionary in JSON format:
    with open(args.json_out, 'w') as f:
        json.dump(annotations, f)