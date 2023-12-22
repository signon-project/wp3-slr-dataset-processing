import os 
import csv
import argparse
import subprocess

def _extract_clip(source, start_ms, end_ms, out_dir):
    start_ms = int(float(start_ms))
    end_ms = int(float(end_ms))

    #Name outfile:
    vid_name = os.path.basename(source)
    out_name = f"{start_ms}_{end_ms}_{vid_name[:-4]}.mp4"

    out_vid = os.path.join(out_dir, out_name)
    
    if os.path.isfile(out_vid):
        return

    #Get width and height of videos as these differ: 
    res = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", source], capture_output=True, text=True)
    info = res.stdout.split(',')
    w = int(info[0])
    h = int(info[-1].split('\\')[0])

    #Create clip:
    subprocess.run(["ffmpeg", "-i", source, "-ss", f"{start_ms}ms", "-to", f"{end_ms}ms",
         "-filter:v", f"fps=25, crop={w}:{h}:0:0", out_vid])

    return out_name


def main(args):

    with open(args.csv_in) as data:
        reader = csv.reader(data)

        _header = next(reader)
        if not _header == ['video_name', 'start_ms', 'end_ms', 'Subset', 'Participant', 'Label']:
            raise Exception("CSV not in correct form. Check column values.")

        out_samples = []
        Id = 0
        for row in reader:
            video_name, start_ms, end_ms, subset, participant, label = row

            clip_name = _extract_clip(os.path.join(args.data_dir, video_name), start_ms, end_ms, args.out_dir)

            out_samples.append([Id, label, participant, clip_name, subset])
            Id += 1

    with open(args.csv_out, 'w') as output_samples_csv:
        writer = csv.writer(output_samples_csv)
        writer.writerow(['Id', 'Label', 'Participant', 'Video', 'Subset'])
        for sample in out_samples:
            writer.writerow(sample)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--data_dir', type=str, help='Path to data directory containing original videos.')
    parser.add_argument('--csv_in', type=str, help='Input .csv file from create_dataset.py step.')
    parser.add_argument('--out_dir', type=str, help='Path to clips directory.')
    parser.add_argument('--csv_out', type=str, help='Output .csv file.')

    args = parser.parse_args()

    main(args)