#!/usr/bin/env python

"""
Author: Lori Garzio on 2/26/2025
Modified from code written by Jessica Leonard
Last modified: 3/18/2025
After using the d3read software to process raw DMON .dtg files to .wav files, this script
sorts and renames the .wav files based on the deployment start and end times.
First, determines which .wav files contain deployment data based 
on the timestamps in the .xml files and saves those files to a new directory for archiving. 
Also determines which files need to be split up (potentially the first and last files) to 
remove some non-deployment data. Move those files to a new directory to split using
Mark Baumgartner's reformat_dmon_wav_files.sav program.
"""

import os
import requests
import datetime as dt
import numpy as np
import pandas as pd
import shutil


def main(filedirectory, deployment):
    savedir = os.path.join(filedirectory, 'files_to_archive')
    savedir_split = os.path.join(filedirectory, 'files_to_split')
    os.makedirs(savedir, exist_ok=True)
    os.makedirs(savedir_split, exist_ok=True)

    # preemptively add a split_files directory for the reformat_dmon_wav_files.sav to save files
    # this will be empty until the files are split using Mark's program
    os.makedirs(os.path.join(filedirectory, 'split_files'), exist_ok=True)

    # grab the deployment start and end times from the API
    glider_api = 'https://marine.rutgers.edu/cool/data/gliders/api/'
    deployment_api = requests.get(f'{glider_api}deployments/?deployment={deployment}').json()['data'][0]
    deployment_start = dt.datetime.fromtimestamp(deployment_api['start_date_epoch'], dt.timezone.utc)
    deployment_end = dt.datetime.fromtimestamp(deployment_api['end_date_epoch'], dt.timezone.utc)
    print(f'Deployment start: {deployment_start}, end: {deployment_end}')

    # list .xml metadata files and find the minimum and maximum timestamps
    # make a dataframe and figure out which files contain deployment data
    cols = ['filename', 'start_time', 'end_time', 'split_file', 'deploy_start', 'deploy_end', 'diff_hours']
    rows = []
    xml_timefmt = '%Y,%m,%d,%H,%M,%S'
    xmlfiles = sorted([x for x in os.listdir(filedirectory) if x.endswith('.xml')])
    for i, f in enumerate(xmlfiles):
        xml_path = os.path.join(filedirectory, f)
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
        # split the files if they contain more than 3 hours of data outside of the deployment start/end times
        if (xml_start <= deployment_end) and (xml_end >= deployment_start):
            split = ''
            dstart = ''
            dend = ''
            tdiff_hours = 0
            if xml_start < deployment_start:
                tdiff_hours = (deployment_start - xml_start).total_seconds() / 60 / 60
                if tdiff_hours > 3:
                    split = 'split_start'
                    dstart = deployment_start
            if xml_end > deployment_end:
                tdiff_hours = (xml_end - deployment_end).total_seconds() / 60 / 60
                if tdiff_hours > 3:
                    split = 'split_end'
                    dend = deployment_end
            rows.append([f, xml_start, xml_end, split, dstart, dend, str(np.round(tdiff_hours, 2))])

    df = pd.DataFrame(rows, columns=cols)
    dfsavefile = os.path.join(filedirectory, f'{deployment}_dmon_wav_files_summary.csv')
    df.to_csv(dfsavefile, index=False)
    print(f'Saved summary file to {dfsavefile}')

    # check the timestamps in the .xml files to determine if the .wav files need to be split
    save_timefmt = '%Y%m%dT%H%M%S'
    for i, row in df.iterrows():
        xml_start = row['start_time']
        xml_end = row['end_time']
    
        # find all of the files associated with the current .xml file, rename them, and save them to a new directory
        associated_files = [x for x in os.listdir(filedirectory) if row['filename'].split('.')[0] in x]
        for af in associated_files:
            af_path = os.path.join(filedirectory, af)
            orig_file_suffix = os.path.splitext(af)[0].split('_')[-1]
            file_ext = os.path.splitext(af)[-1]
            # af_newname = f'{deployment}_{xml_start.strftime(save_timefmt)}_{xml_end.strftime(save_timefmt)}_{orig_file_suffix}{file_ext}'
            af_newname = f'{deployment}_{orig_file_suffix}{file_ext}'

            # for files that need to be split, put them in a different directory
            if row['split_file'] in ['split_start', 'split_end']:
                output_path = os.path.join(savedir_split, af_newname)
            else:
                output_path = os.path.join(savedir, af_newname)
            
            if file_ext == '.dtg':  # don't archive .dtg files
                continue
            else:
                shutil.move(af_path, output_path)
                print(f'Copied {af} to {af_newname}')

    print('Finished sorting files')
    

if __name__ == '__main__':
    filedir = '/Users/garzio/Documents/gliderdata/ru40-20230629T1430/from-dmon'
    deployment = 'ru40-20230629T1430'
    main(filedir, deployment)
