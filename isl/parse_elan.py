from pympi.Elan import Eaf as eaf
import pandas as pd
import json
import glob
import cv2
import os
import argparse

def _elan_to_dict(annotation_filename):
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
    video_path = os.path.join(*annotation_eaf.get_linked_files()[0]['MEDIA_URL'].split('/')[-2:])
    
    # Get annotation list from each tier of this EAF file and put it into a dictionary 
    annotation_tier_dict = dict()
    for tier_name in annotation_eaf.get_tier_names():
        annotation_tier_dict[tier_name] = annotation_eaf.get_annotation_data_for_tier(tier_name)
        
    # Return a dictionary with annotation information  
    return {"relative_video_path": video_path, 
                       "video_format": video_format,
                       "annotations": annotation_tier_dict
                      }


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--eaf_root', type=str, help='Root dir of the SoI corpus .eaf files.')
    parser.add_argument('--video_root', type=str, help='Root dir of the SoI corpus video files.')
    parser.add_argument('--json_out', type=str, help='Output .json file of parsed results.')
    parser.add_argument('--errors_out', type=str, help='Output .csv file of errors.')

    args = parser.parse_args()

    error_video_files = []
    exceptions = []

    #1.  Get all EAF files from the stated directory:
    eaf_files =sorted(glob.glob(os.path.join(args.eaf_root, '*.eaf')))
    eaf_files_dict = dict()

    #2. Parse ELAN files:
    for annotation_filename in eaf_files:
        # We use this try-except to capture errors in video and EAF files. 
        # We collect these errors as we go along. 
        try:
            # Get dictionary of EAF file. 
            file_annotation_dict  = _elan_to_dict(annotation_filename)
            # Create the dictionary to record misaligned labels. 
            misaligned_annotations = {tier_name:[] for tier_name in file_annotation_dict["annotations"].keys()}
            video_path = os.path.join(args.video_root, file_annotation_dict["relative_video_path"])
            # Check if the video at video path does not exists. 
            if not os.path.isfile(video_path):
                # If not, get the relative path without the file extension. 
                relative_base =  file_annotation_dict["relative_video_path"].split('.')[0]
                # Get the filename without the file extension. 
                filename_base = os.path.split(relative_base)[-1]
                # Check if the video has, in fact, been converted using the convention of other 
                # files in the same directory. 
                relative_mov = os.path.join("Personal Stories", filename_base)+" (Converted).mov"
                # Update to correct video path.
                file_annotation_dict["relative_video_path"] = relative_mov
                # Update to correct video format (".mov" is Quicktime format).
                file_annotation_dict["video_format"] = "video/quicktime"
                # Update the video path. 
                video_path = os.path.join(args.video_root, relative_mov)
                # If this videp doesn't exist either, raise exception that can be noted later.
                if  not os.path.isfile(video_path):
                    raise Exception("File does not exist!")
            # Check if video loads correctly (i.e. not corrupted).
            video = cv2.VideoCapture(video_path)
            FPS = video.get(cv2.CAP_PROP_FPS)
            file_annotation_dict["fps"] = FPS
            num_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
            # If no frames are loaded (video empty or fails silently) raise exception. 
            if num_frames == 0:
                raise Exception("File did not load correctly, no frames returned.")
            video.release()

            # Iterate over each tier of annoations. 
            for tier_name in file_annotation_dict["annotations"].keys():
                # list for all the annotation in this tier. 
                tier_annotation_list = []
                # Iterate over all the annotations in this tier
                for anno_i in file_annotation_dict["annotations"][tier_name]:
                    # Check if annotation is in the video. 
                    anno_in_vid = False
                    # Annotations are in the following format [start_fime, end_time, label]
                    start_time = int(anno_i[0])
                    end_time = int(anno_i[1])
                    # This calculates the millisecond value of the last frame in the video 
                    # (explanation on line 116)
                    last_frame_idx = num_frames
                    last_frame_ms_val = int((last_frame_idx/FPS)*1000)
                    for i in range(int(num_frames)):         
                        # frame index (i.e. frame number)/ frames per second = fraction of a second 
                        # that the current frame is at.
                        # Obviously 1000 = number of milliseconds per second so multiplying by 
                        # 1000 tells us at what millisecond the frame is at.
                        # This means that we go to the part of the video where the sign starts.
                        ms_val = int(((i+1)/FPS)*1000)
                        # There are some situations where the label is actually somehow BETWEEN frames for some reason. 
                        # The label should also not go beyond the end of the video itself. 
                        if (ms_val >= start_time) and (ms_val <= end_time) and not (end_time >= last_frame_ms_val):
                            anno_in_vid = True
                    # This is necessary to avoid errors when labels have been misaligned,
                    # i.e. their are no frames within the time period the annotation describes,
                    # This could be due to low framerate or, more likely, due to misalignment for 
                    # annotations of events occuring for a very short period of time. 
                    if anno_in_vid :
                        tier_annotation_list.append(anno_i)
                    else:
                        misaligned_annotations[tier_name].append(anno_i)
                # Replace annotations with those without the misaligned annotations. 
                file_annotation_dict["annotations"][tier_name] = tier_annotation_list
                # Add the list of misaligned annotations from this EAF file to the new annotation dictionary. 
                file_annotation_dict["misaligned_annotations"] = misaligned_annotations
                # Add new cleaned annotation dictionary to the overall annotation dictionary
                # under the name of the original EAF file. 
                eaf_files_dict[annotation_filename] = file_annotation_dict
        # If an exception occurs, flag this and collect the name of the video within which this occured and
        # a description of the error that occured. 
        except Exception as e: 
            print(f"Handled exception when processing eaf file {annotation_filename} or video file {video_path}: {e}")
            error_video_files.append(video_path)
            exceptions.append(e)

    #3. Save errors to a CSV:
    df = pd.DataFrame(index=error_video_files)
    df["error"] = exceptions
    df.to_csv(args.errors_out)

    #4. Write cleaned annotation dictionaries to JSON format:
    with open(args.json_out, 'w') as f:
        json.dump(eaf_files_dict, f)
