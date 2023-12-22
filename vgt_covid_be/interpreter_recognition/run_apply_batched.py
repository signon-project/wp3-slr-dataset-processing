import glob
import json
import os

metadata_files = glob.glob('/project/signon_covid_annotation/metadata/*.json')

print(f'Found {len(metadata_files)} metadata files...')

ftp_password = os.environ['SIGNON_FTP_PASS']
for f in metadata_files:
    with open(f) as metafile:
        metadata = json.loads(metafile.read())
        if 'bounding_box' not in metadata:
            continue  # Not yet processed

        checkpoint = '/project/signon_covid_annotation/logs/checkpoint_99.pth'
        ftp_url = f"sftp://signon:{ftp_password}@sftp.signon.ivdnt.org/private/SignLanguage/VGT/VGT_Covid_BE/" + os.path.basename(f).replace('.json', '.mp4')
        start = metadata['start']
        bounding_box = metadata['bounding_box']
        bb = f'{bounding_box["x"]},{bounding_box["y"]},{bounding_box["width"]},{bounding_box["height"]}'
        lang = metadata['language']
        out = f'/project/signon_covid_annotation/auto_annotations/{os.path.basename(f)}'
        os.makedirs('/project/signon_covid_annotation/auto_annotations', exist_ok=True)
        device = 'cuda'
        batch_size = 128
        interpreter = metadata['interpreter']
        os.system(f'python apply_batched.py -c {checkpoint} -i {ftp_url} ' 
                  f'-s {start} -b {bb} -t 1 -a {lang} -o {out} -d {device} -z {batch_size} -n {interpreter}')
