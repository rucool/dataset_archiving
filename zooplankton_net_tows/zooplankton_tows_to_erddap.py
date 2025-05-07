#!/usr/bin/env python

"""
Author: Lori Garzio on 4/30/2025
Last modified: 5/1/2025
Format zooplankton net tow data to netcdf for sharing in ERDDAP
https://rucool-sampling.marine.rutgers.edu/erddap/index.html
These datasets are sorted by project.
"""

import datetime as dt
import glob
import numpy as np
import pandas as pd
import yaml
import os
pd.set_option('display.width', 320, "display.max_columns", 15)  # for display in pycharm console


def convert_lat_lon(data_degrees, data_decimal_minutes):
    value = np.sign(data_degrees) * (abs(data_degrees) + (data_decimal_minutes / 60))

    return value


def main(proj):
    rootdir = os.path.dirname(os.path.abspath(__file__))
    savefile = os.path.join(rootdir, 'output', f'{proj}_zooplankton_tows_erddap.nc')

    gattrs = os.path.join(rootdir, 'config', f'global_attrs_{proj}.yml')
    vattrs = os.path.join(rootdir, 'config', f'variable_attrs_{proj}.yml')

    with open(gattrs) as stream:
        ga = yaml.safe_load(stream)
    with open(vattrs) as stream:
        va = yaml.safe_load(stream)

    files = sorted(glob.glob(os.path.join(rootdir, 'files', proj, '*.csv')))
    df = pd.concat((pd.read_csv(f) for f in files), ignore_index=True)

    # format dataset
    # format time, lon, lat, calculate tow duration
    df['time'] = pd.to_datetime(df.date_utc + df.time_utc_start, format='%m/%d/%Y%H:%M')
    end_time = pd.to_datetime(df.date_utc + df.time_utc_end, format='%m/%d/%Y%H:%M')
    diff = end_time - df['time']
    df['tow_duration'] = diff.dt.total_seconds() / 60  # convert to minutes
    df['latitude'] = convert_lat_lon(df.lat_degrees_start, df.lat_mins_start)
    df['longitude'] = convert_lat_lon(df.lon_degrees_start, df.lon_mins_start)
    df['latitude_end'] = convert_lat_lon(df.lat_degrees_end, df.lat_mins_end)
    df['longitude_end'] = convert_lat_lon(df.lon_degrees_end, df.lon_mins_end)

    # drop columns
    drop_cols = ['date_utc', 'time_utc_start', 'time_utc_end', 'lat_degrees_start', 'lat_mins_start', 
                 'lon_degrees_start', 'lon_mins_start', 'lat_degrees_end', 'lat_mins_end',
                 'lon_degrees_end', 'lon_mins_end']
    df.drop(drop_cols, axis=1, inplace=True)
    df = df.set_index('time')
    df = df.sort_index()
    strcols = ['glider_trajectory', 'acoustics_configuration', 'deployment_recovery', 'season', 'sample_notes', 'taxa', 'taxa_group']  # columns that are strings
    
    # fill nans in columns that aren't strings with -9999
    df[[col for col in df.columns if col not in strcols]] = df[[col for col in df.columns if col not in strcols]].fillna(-9999)

    # reorder columns
    sortcols = ['latitude', 'longitude', 'latitude_end', 'longitude_end', 'tow_duration']
    column_order = sortcols + [col for col in df.columns if col not in sortcols]
    df = df[column_order]

    # rename some columns
    rename_cols = {'net_depth': 'depth',
                   'temp_min': 'temperature_min', 
                   'temp_max': 'temperature_max',
                   'sal_min': 'salinity_min', 
                   'sal_max': 'salinity_max'}
    df.rename(columns=rename_cols, inplace=True)

    ds = df.to_xarray()

    for variable in list(ds.data_vars):
        try:
            ds[variable].attrs = va[variable]['attrs']
        except KeyError:
            continue
        try:  # round to specified number of decimal places
            ds[variable].values = np.round(ds[variable].values, va[variable]['decimal'])
            if va[variable]['decimal'] == 0:
                ds[variable].values = ds[variable].values.astype(int)
        except KeyError:
            continue

    encoding = dict()

    for k in ds.data_vars:
        if k in strcols:
            encoding[k] = dict(zlib=False, dtype=object, _FillValue=None)
        elif k in ['tow_number', 'tow_duration', 'water_column_depth', 'depth', 'count']:
            encoding[k] = dict(zlib=True, dtype=np.int32, _FillValue=np.int32(-9999))
        else:
            encoding[k] = dict(zlib=True, dtype=np.float32, _FillValue=np.float32(-9999.0))

    # add the encoding for time so xarray exports the proper time
    encoding["time"] = dict(calendar="gregorian", zlib=False, _FillValue=None, dtype=np.double)

    ds = ds.assign_attrs(ga)

    ds.to_netcdf(savefile, encoding=encoding, format="netCDF4", engine="netcdf4")


if __name__ == '__main__':
    project = 'RMI'
    main(project)
