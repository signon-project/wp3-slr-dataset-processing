import argparse
import os
import json
import glob

ftp_password = os.environ['SIGNON_FTP_PASS']
FFMPEG_STR = 'ffmpeg -i sftp://signon:{}@sftp.signon.ivdnt.org/private/SignLanguage/VGT/VGT_Covid_BE/{} -ss {} -to {} -vf fps=25 -filter:v "crop={}:{}:{}:{}" {}.mp4'


def get_ffmpeg_str(video_file, from_seconds, to_seconds, width, height, x, y, output_filename):
    return FFMPEG_STR.format(ftp_password, video_file, from_seconds, to_seconds, width, height, x, y, output_filename)


def get_lsfb_segments(vgt_segments):
    """Get all segments in between VGT segments as LSFB segments.
    """
    start_times = [segment['start'] for segment in vgt_segments]
    end_times = [segment['end'] for segment in vgt_segments]

    lsfb_segments = []
    for index in range(0, len(start_times) - 1):
        start_lsfb = end_times[index]
        end_lsfb = start_times[index + 1]
        lsfb_segments.append({
            'start': start_lsfb,
            'end': end_lsfb
        })
    return lsfb_segments


def get_output_filename(root_output_dir, video_filename, segment_index, language):
    # e.g., out/FOD_20200313__VGT_2.mp4
    output_filename = os.path.join(root_output_dir, f'{video_filename.replace(".mp4", "")}__{language}_{segment_index}')
    return output_filename


def process_video(json_file, root_output_dir):
    with open(json_file, 'r') as json_file:
        annotations = json.loads(json_file.read())
        vgt_segments = annotations['signing_times']
        lsfb_segments = get_lsfb_segments(vgt_segments)

        crop_box = annotations['interpreter_bounding_box']

        for i, segment in enumerate(vgt_segments):
            ffmpeg_str = get_ffmpeg_str(annotations['filename'],
                                        segment['start'],
                                        segment['end'],
                                        crop_box['width'],
                                        crop_box['height'],
                                        crop_box['x'],
                                        crop_box['y'],
                                        get_output_filename(root_output_dir, annotations['filename'], i, 'VGT'))
            os.system(ffmpeg_str)
        
        for i, segment in enumerate(lsfb_segments):
            ffmpeg_str = get_ffmpeg_str(annotations['filename'],
                                        segment['start'],
                                        segment['end'],
                                        crop_box['width'],
                                        crop_box['height'],
                                        crop_box['x'],
                                        crop_box['y'],
                                        get_output_filename(root_output_dir, annotations['filename'], i, 'LSFB'))
            os.system(ffmpeg_str)


def main(args):
    input_files = sorted(glob.glob(os.path.join(args.input_dir, 'FOD_*.json')))
    for i, input_file in enumerate(input_files):
        print(f'Processing {input_file} ({i}/{len(input_files)})', end='\r')
        print(input_file)
        process_video(input_file, args.output_dir)


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()

    arg_parser.add_argument('-i', '--input-dir')
    arg_parser.add_argument('-o', '--output-dir')

    args = arg_parser.parse_args()

    main(args)
