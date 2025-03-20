#!/usr/bin/env python

"""
Author: Lori Garzio on 3/17/2025
Last modified: 3/20/2025
After splitting DMON .wav files (entire deployment) using Mark Baumgartner's reformat_dmon_wav_files.sav program,
this script 1. figures out which split files need to be sorted (e.g. files from the beginning and/or end of the deployment),
2. compares the timestamp in those filenames to the glider deployment start and end times.
If a file contains deployment data, it is saved to the "files_to_archive" directory. The .wav files that didn't 
need to be split are deleted.
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

    # read in the summary .csv file generated by sort_dmon_wav_files.py to figure out which files needed to be split
    csvfilename = os.path.join(os.path.dirname(filedirectory), f'{deployment}_dmon_wav_files_summary.csv')
    df = pd.read_csv(csvfilename)
    df = df[df['split_file'].notna()]
    files_to_sort = [os.path.splitext(x)[0] for x in df.filename.tolist()]  # remove the extension from the filename

    # list .wav files
    # split filenames have timestamps in the format YYYYMMDDhhmmss_uuuuuu.wav where YYYY is year, MM is month, DD is day,
    # hh is hour, mm is minute, ss is second, and uuuuuu is microseconds
    wav_files = [x for x in os.listdir(filedirectory) if x.endswith('.wav')]
    
    # make a list of files that need to be sorted based on the summary .csv file (since we had to split the entire deployment,
    # we only need to archive the split files fromt he deployment and/or recovery that might contain non-deployment data)
    files = []
    for fts in files_to_sort:
        add_files = [x for x in wav_files if fts in x]
        files.extend(add_files)
    files = sorted(files)  # make sure the files are sorted in chronological order
    
    # move the files with timestamps that fall within the deployment start and end times to the "files_to_archive" directory
    count = 0
    for i, f in enumerate(files):
        ts = pd.to_datetime(f.split('_')[-2]).tz_localize('UTC')  # get the timestamp from the filename
        if (ts <= deployment_end) and (ts >= deployment_start):
            # move the file to the archiving folder
            shutil.move(os.path.join(filedirectory, f), os.path.join(savedir, f))
            count += 1
        # if the file from the beginning of the deployment needed to be split, also grab the file before the first file
        # within the deployment time range to archive (it presumably contains deployment data)
        if 'split_start' in df.split_file.tolist():
            if count == 1:
                f = files[i-1]
                shutil.move(os.path.join(filedirectory, f), os.path.join(savedir, f))
                count += 1

    # delete the extra split files that were created by the reformat_dmon_wav_files.sav program
    files_to_delete = set(wav_files) - set(files)
    for ftd in files_to_delete:
        os.remove(os.path.join(filedirectory, ftd))

    print('Finished sorting split files')
    

if __name__ == '__main__':
    filedir = '/Users/garzio/Documents/gliderdata/ru40-20240429T1528/from-dmon/split_files'
    # filedir = 'C:/Users/rucool/Documents/DMON/2024/ru40-20240429T1528/from-dmon/split_files'  # PC directory
    deployment = 'ru40-20240429T1528'
    main(filedir, deployment)
