import numpy as np 
import pandas as pd
import json
import cv2
import os
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--video_root', type=str, help='Root dir of the SoI corpus video files.')
    parser.add_argument('--anno_json', type=str, help='Output .json file from parse_elan.py.')
    parser.add_argument('--clean_dir', type=str, help='Output directory for cleaned data.')

    args = parser.parse_args()

with open(args.anno_json, 'r') as f:
    eaf_files_dict = json.load(f)
    
for eaf_filename in eaf_files_dict.keys():
    print(f"Processing eaf file: {eaf_filename}")
    video_path = os.path.join(args.video_root, eaf_files_dict[eaf_filename]['relative_video_path'])
    video = cv2.VideoCapture(video_path)
    FPS = video.get(cv2.CAP_PROP_FPS)
    num_frames = video.get(cv2.CAP_PROP_FRAME_COUNT)   

    # Get video path without file extension
    file_path_wo_file_ex =  eaf_files_dict[eaf_filename]['relative_video_path'].split('.')[0]
    # Separate path and rejoin in case someone is on Windows
    file_path_wo_file_ex_split = os.path.split(file_path_wo_file_ex)
    # Get the directory the video is in and the video filename separately (we'll use these later)
    file_dir, filename = file_path_wo_file_ex_split[0], file_path_wo_file_ex_split[1]
    # New directory for frames of video. 
    new_frames_dir = os.sep.join([args.clean_dir, file_dir, filename ])
    if not os.path.exists(new_frames_dir): os.makedirs(new_frames_dir)
    frame_count = 0
    # Obtain the annotation information for this specific EAF file. 
    eaf_file_dict = eaf_files_dict[eaf_filename]
    print(f"\tWriting frames from file: {video_path}")
    for i in range(int(num_frames)):
        # Read a frame from the video and check that this process was successful before continuing. 
        return_val, frame = video.read()                                             
        assert return_val == True
        # Write frames to a directory named after the orginial video. Each video has the frame number 
        # as denoted by the frame_count counter. 
        cv2.imwrite(os.path.join(new_frames_dir,  "{filename}_frame_{frame_count}.jpg"), frame) 
        frame_count+=1 
    # Release current video. 
    video.release()
    # Create a dataframe for the label of each frame. 
    label_dataframe = pd.DataFrame()
    # Go through annotation tiers for video. 
    for label_tier in eaf_file_dict["annotations"].keys():
        # Create an empty array with an inital label value of 'Nan' for each frame in the video.
        tier_annos_array = ["Nan" for _ in range(frame_count)]
        # Get all annotations for this specific tier. 
        tier_annos = eaf_file_dict["annotations"][label_tier]
        for anno in tier_annos:
            # Annotations are formatted as "[start_time, end_time, label]"
            start_time = anno[0]
            # Start_time is in ms, so we first divide by 1000 to get the second value. Then we multiply by 
            # the Frames per second to find out what frame index this second value is at. 
            start_time_frame_i = int((start_time/1000)*FPS)
            end_time = anno[1]
            end_time_frame_i = int((end_time/1000)*FPS)
            label = anno[2:]  
            label = '\t'.join(label)
                
            # This will give this label to frames from and including the start time up until
            # up to and including the end time (This might be something that needs to change).
            # reference: https://stackoverflow.com/questions/11395057/python-set-list-range-to-a-specific-value
            tier_annos_array[start_time_frame_i:(end_time_frame_i+1)] = [label]*((end_time_frame_i+1) - start_time_frame_i) 
            # Check that the number of video frames is equal to the number of labels in this tier's array. 
            assert len(tier_annos_array) == frame_count
        # Create a column with the name of the current tier and add the array of label values to this column. 
        label_dataframe[label_tier] =  tier_annos_array
    # Write these anootations out to a CSV after adding labels for all tiers. 
    label_dataframe.to_csv(os.path.join(new_frames_dir, filename+"_labels.csv"), index=False)
    
