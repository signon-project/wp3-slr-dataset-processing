import glob
import json
import os

metadata_files = glob.glob('../metadata/*.json')
ftp_password = os.environ['SIGNON_FTP_PASS']

for f in metadata_files:
    with open(f) as metafile:
        metadata = json.loads(metafile.read())
        if 'bounding_box' in metadata:
            continue  # Already processed

        print(f)

        FTP_URL = f"sftp://signon:{ftp_password}@sftp.signon.ivdnt.org/private/SignLanguage/VGT/VGT_Covid_BE/" + os.path.basename(f).replace('.json', '.mp4')
        os.system(f'python get_metadata.py -i {FTP_URL} -m {f}')
