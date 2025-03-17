#!/usr/bin/env python

"""
Author: Lori Garzio on 3/17/2025
Last modified: 3/17/2025
After splitting DMON .wav files using Mark Baumgartner's reformat_dmon_wav_files.sav program,
this script compares the timestamp in the filename to the glider deployment start and end times.
If a file contains deployment data, it is saved to a new directory for archiving.
"""

import os
import requests
import datetime as dt
import numpy as np
import pandas as pd
import shutil


def main(filedirectory, deployment):
    savedir = os.path.join(os.path.dirname(filedirectory), 'files_to_archive')
    os.makedirs(savedir, exist_ok=True)

    # grab the deployment start and end times from the API
    glider_api = 'https://marine.rutgers.edu/cool/data/gliders/api/'
    deployment_api = requests.get(f'{glider_api}deployments/?deployment={deployment}').json()['data'][0]
    deployment_start = dt.datetime.fromtimestamp(deployment_api['start_date_epoch'], dt.timezone.utc)
    deployment_end = dt.datetime.fromtimestamp(deployment_api['end_date_epoch'], dt.timezone.utc)
    print(f'Deployment start: {deployment_start}, end: {deployment_end}')

    # list .wav files and get timestamps from the filenames
    # split filenames have timestamps in the format YYYYMMDDhhmmss_uuuuuu.wav where YYYY is year, MM is month, DD is day,
    # hh is hour, mm is minute, ss is second, and uuuuuu is microseconds
    # move the files with timestamps that fall within the deployment start and end times to the "files_to_archive" directory
    count = 0
    files = sorted([x for x in os.listdir(filedirectory) if x.endswith('.wav')])
    for i, f in enumerate(files):
        ts = pd.to_datetime(f.split('_')[-2]).tz_localize('UTC')
        if (ts <= deployment_end) and (ts >= deployment_start):
            # move the file to the archiving folder
            shutil.move(os.path.join(filedirectory, f), os.path.join(savedir, f))
            count += 1
        if count == 1:
            # grab the file before the first file within the deployment time range to also archive 
            # (it presumably contains deployment data)
            f = files[i-1]
            shutil.move(os.path.join(filedirectory, f), os.path.join(savedir, f))
            count += 1

    print('Finished sorting split files')
    

if __name__ == '__main__':
    filedir = '/Users/garzio/Documents/gliderdata/ru40-20230629T1430/from-dmon/split_files'
    deployment = 'ru40-20230629T1430'
    main(filedir, deployment)
