#!/usr/bin/env python

"""
Author: Lori Garzio on 2/11/2025
Last modified: 8/19/2025
Download a user-specified glider dataset in netCDF format from RUCOOL's glider ERDDAP server and save to a local
directory
"""

import numpy as np
import os
import yaml
import time
import dataset_archiving.common as cf


def flatten(lst):
    return [item for sublist in lst for item in sublist]


def main(deploy, version, aev, sdir):
    start_time = time.time()  # Record the start time
    dsid = f'{deploy}-{version}'

    sdir = os.path.join(sdir, deploy)
    os.makedirs(sdir, exist_ok=True)
    ru_server = 'https://slocum-data.marine.rutgers.edu/erddap'

    ds_vars = cf.get_dataset_variables(ru_server, dsid)

    root_dir = os.path.dirname(os.path.abspath(__file__))
    configdir = os.path.join(root_dir, 'configs')

    # start with the standard glider variables
    with open(os.path.join(configdir, 'glider_standard_vars.yml')) as f:
        glider_vars = [yaml.safe_load(f)]

    # add science variables
    with open(os.path.join(configdir, f'glider_sci_vars.yml')) as f:
        sensor_vars = yaml.safe_load(f)
    for sv in sensor_vars:
        if sv in ds_vars:
            glider_vars.append([sv])
        # add unshifted oxygen if shifted isn't available
        if sv in ['oxygen_concentration_shifted', 'oxygen_saturation_shifted']:
            if sv not in ds_vars:
                if sv.replace('_shifted', '') in ds_vars:
                    glider_vars.append([sv.replace('_shifted', '')])
    
    # add all of the instrument metadata vars
    instrument_vars = [x for x in ds_vars if 'instrument_' in x]
    glider_vars.append(instrument_vars)

    # add QC flags
    qcflagvars = ['_qartod_summary_flag', '_hysteresis_test']
    for qc in qcflagvars:
        addqcvars = [x for x in ds_vars if qc in x]
        glider_vars.append(addqcvars)

    # add extra engineering variables if specified
    if aev:
        with open(os.path.join(configdir, f'glider_engineering_vars.yml')) as f:
            engvars = yaml.safe_load(f)
        glider_vars.append(engvars)

    glider_vars = flatten(glider_vars)
    glider_vars = np.unique(glider_vars).tolist()

    # request dataset and save the .nc file to a local directory
    kwargs = dict()
    kwargs['variables'] = glider_vars
    ds = cf.return_erddap_nc(ru_server, dsid, **kwargs)
    fname = f'{dsid}.nc'
    ds.to_netcdf(os.path.join(sdir, fname))

    end_time = time.time()  # Record the end time
    elapsed_time = (end_time - start_time) / 60 # Calculate the elapsed time in minutes
    print(f"Time elapsed: {elapsed_time:.2f} minutes")  # Print the elapsed time


if __name__ == '__main__':
    deployment = 'ru39-20240429T1522'
    version = 'profile-sci-delayed'
    add_engineering_vars = True  # True False
    savedir = '/Users/garzio/Documents/gliderdata'
    main(deployment, version, add_engineering_vars, savedir)
