#!/usr/bin/env python

"""
Author: Lori Garzio on 2/26/2025
Modified from code written by Jessica Leonard
Last modified: 3/20/2025
After using the d3read software to process raw DMON .dtg files to .wav files, this script
1. renames the files to contain the deployment ID and moves those to a folder called "renamed"
2. reads in the .xml metadata files to determine which .wav files contain deployment data
3. determines if the .wav files need to be split based on the timestamps in the .xml files (a files
   needs to be split if it contains more than 6 hours of data outside of the deployment start/end times)
4. spits out a summary .csv file
5. if a file contains deployment data and doesn't need to be split, moves the files to directory "files_to_archive"

If there are files that must be split, use Mark Baumgartner's reformat_dmon_wav_files.sav program.
"""

import os
import requests
import datetime as dt
import numpy as np
import pandas as pd
import shutil


def main(filedirectory, deployment):
    savedir = os.path.join(filedirectory, 'files_to_archive')
    savedir_rename = os.path.join(filedirectory, 'renamed')
    os.makedirs(savedir, exist_ok=True)
    os.makedirs(savedir_rename, exist_ok=True)

    # preemptively add a split_files directory for the reformat_dmon_wav_files.sav to save files
    # this will be empty until the files are split using Mark's program
    os.makedirs(os.path.join(filedirectory, 'split_files'), exist_ok=True)

    # grab the deployment start and end times from the API
    glider_api = 'https://marine.rutgers.edu/cool/data/gliders/api/'
    deployment_api = requests.get(f'{glider_api}deployments/?deployment={deployment}').json()['data'][0]
    deployment_start = dt.datetime.fromtimestamp(deployment_api['start_date_epoch'], dt.timezone.utc)
    deployment_end = dt.datetime.fromtimestamp(deployment_api['end_date_epoch'], dt.timezone.utc)
    print(f'Deployment start: {deployment_start}, end: {deployment_end}')

    # rename the files to include the deployment ID
    extensions = ['.wav', '.xml', '.dtg', '.log', '.err']
    files = sorted([x for x in os.listdir(filedirectory) if os.path.isfile(os.path.join(filedirectory, x)) and os.path.splitext(x)[-1] in extensions])
    for f in files:
        orig_file_suffix = os.path.splitext(f)[0].split('_')[-1]
        file_ext = os.path.splitext(f)[-1]
        f_newname = f'{deployment}_{orig_file_suffix}{file_ext}'
        shutil.copy(os.path.join(filedirectory, f), os.path.join(savedir_rename, f_newname))
        print(f'Renamed {f} to {f_newname}')

    # list .xml metadata files and find the minimum and maximum timestamps
    # make a dataframe and figure out which files contain deployment data
    cols = ['filename', 'start_time', 'end_time', 'split_file', 'deploy_start', 'deploy_end', 'diff_hours']
    rows = []
    xml_timefmt = '%Y,%m,%d,%H,%M,%S'
    xmlfiles = sorted([x for x in os.listdir(savedir_rename) if x.endswith('.xml')])
    for i, f in enumerate(xmlfiles):
        xml_path = os.path.join(savedir_rename, f)
        xml_data = pd.read_xml(xml_path, parser='etree')
        xml_data['TS'] = pd.to_datetime(xml_data['TIME'], format=xml_timefmt)
        xml_times = pd.to_datetime(xml_data['TIME'], format=xml_timefmt).dropna()

        # CUE TIME is the start time of the recording
        start = xml_data['TS'][np.logical_and(xml_data['SUFFIX']=='wav',~np.isnan(xml_data['CUE']))].item()
        xml_start = pd.to_datetime(start).tz_localize('UTC').round('s')

        # assume the end time of the recording is the max timestamp in the .xml file
        xml_end = pd.to_datetime(np.nanmax(xml_times)).tz_localize('UTC').round('s')
        print(f'file: {f}, start time: {xml_start}, end time: {xml_end}')

        # if the time range in the xml file overlaps with the deployment time range, figure out if the file needs
        # to be split and add to summary df
        # split the files if they contain more than 6 hours of data outside of the deployment start/end times
        if (xml_start <= deployment_end) and (xml_end >= deployment_start):
            split = ''
            dstart = ''
            dend = ''
            tdiff_hours = 0
            if xml_start < deployment_start:
                tdiff_hours = (deployment_start - xml_start).total_seconds() / 60 / 60
                if tdiff_hours > 6:
                    split = 'split_start'
                    dstart = deployment_start
            if xml_end > deployment_end:
                tdiff_hours = (xml_end - deployment_end).total_seconds() / 60 / 60
                if tdiff_hours > 6:
                    split = 'split_end'
                    dend = deployment_end
            rows.append([f, xml_start, xml_end, split, dstart, dend, str(np.round(tdiff_hours, 2))])

    df = pd.DataFrame(rows, columns=cols)
    dfsavefile = os.path.join(filedirectory, f'{deployment}_dmon_wav_files_summary.csv')
    df.to_csv(dfsavefile, index=False)
    print(f'Saved summary file to {dfsavefile}')

    # check the timestamps in the .xml files to determine if the .wav files need to be split
    for i, row in df.iterrows():
        # for files that need to be split, don't put them in the files_to_archive directory
        # those will be added later using sort_split_dmon_wav_files.py
        if row['split_file'] in ['split_start', 'split_end']:
            continue
        else:
            # find all of the files associated with the current .xml file, rename them, and save them to a new directory
            associated_files = [x for x in os.listdir(savedir_rename) if row['filename'].split('.')[0] in x]
            for af in associated_files:
                file_ext = os.path.splitext(af)[-1]
                
                if file_ext == '.dtg':  # don't archive .dtg files
                    continue
                else:
                    shutil.copy(os.path.join(savedir_rename, af), os.path.join(savedir, af))
                    print(f'Copied {af} to "files_to_archive"')

    print('Finished sorting files')
    

if __name__ == '__main__':
    filedir = '/Users/garzio/Documents/gliderdata/ru40-20230629T1430/from-dmon'
    deployment = 'ru40-20230629T1430'
    main(filedir, deployment)
