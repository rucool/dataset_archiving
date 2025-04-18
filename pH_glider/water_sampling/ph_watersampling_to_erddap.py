#!/usr/bin/env python

"""
Author: Lori Garzio on 1/22/2025
Last modified: 4/18/2025
Format pH glider water sampling tables to netcdf for sharing in ERDDAP.
Files are located in the water_sampling directory
"""

import datetime as dt
import glob
import numpy as np
import pandas as pd
import yaml
import xarray as xr
import os
pd.set_option('display.width', 320, "display.max_columns", 15)  # for display in pycharm console


def convert_lat_lon(data_degrees, data_decimal_minutes):
    value = np.sign(data_degrees) * (abs(data_degrees) + (data_decimal_minutes / 60))

    return value


def make_encoding(dataset, fillvalue=-9999.0, datatype=np.float32):
    encoding = dict()

    for k in dataset.data_vars:
        encoding[k] = dict(zlib=True, _FillValue=np.float32(fillvalue), dtype=datatype)

    # add the encoding for time so xarray exports the proper time
    encoding["time"] = dict(calendar="gregorian", zlib=False, _FillValue=None, dtype=np.double)

    return encoding


def main():
    wsdir = os.path.dirname(os.path.abspath(__file__))
    savefile = os.path.join(wsdir, 'output', 'pH_watersampling_erddap.nc')

    gattrs = os.path.join(wsdir, 'config', 'global_attrs.yml')
    vattrs = os.path.join(wsdir, 'config', 'variable_attrs.yml')

    with open(gattrs) as stream:
        ga = yaml.safe_load(stream)
    with open(vattrs) as stream:
        va = yaml.safe_load(stream)

    files = sorted(glob.glob(os.path.join(wsdir, 'files', '*.csv')))
    df = pd.concat((pd.read_csv(f) for f in files), ignore_index=True)

    # format dataset
    # fix time, lon, lat, combine notes
    df['time'] = pd.to_datetime(df.date_utc + df.time_utc, format='%m/%d/%y%H:%M')
    df['latitude'] = convert_lat_lon(df.lat_degrees, df.lat_mins)
    df['longitude'] = convert_lat_lon(df.lon_degrees, df.lon_mins)

    # drop columns
    drop_cols = ['date_utc', 'time_utc', 'lat_degrees', 'lat_mins', 'lon_degrees', 'lon_mins', 'sample',
                 'bottle_size_ml', 'sample_notes', 'analysis_notes']
    df.drop(drop_cols, axis=1, inplace=True)

    # put data collected at the same depth/cast/sample bottle on the same row:
    # split dataframe into 3, drop nans, then merge back together
    ph_dropcols = ['TA_avg', 'TA_stdev', 'DIC_avg', 'DIC_stdev']
    ta_dropcols = ['pH_avg_25degC', 'pH_stdev', 'DIC_avg', 'DIC_stdev']
    dic_dropcols = ['pH_avg_25degC', 'pH_stdev', 'TA_avg', 'TA_stdev']
    df1 = df.drop(ph_dropcols, axis=1)
    df2 = df.drop(ta_dropcols, axis=1)
    df3 = df.drop(dic_dropcols, axis=1)

    df1.dropna(subset=['pH_avg_25degC'], inplace=True)
    df2.dropna(subset=['TA_avg'], inplace=True)
    df3.dropna(subset=['DIC_avg'], inplace=True)

    merge_cols = ['project', 'station_id', 'glider_trajectory', 'deployment_recovery', 'cast', 'niskin', 'depth_m', 
                  'temperature_degrees_c', 'salinity', 'time', 'latitude', 'longitude']
    merged1 = pd.merge(df1, df2, how='outer', on=merge_cols)
    merged = pd.merge(merged1, df3, how='outer', on=merge_cols)
    merged = merged.sort_values(by=['time', 'depth_m'])
    merged = merged.drop_duplicates()
    merged = merged.set_index('time')
    merged = merged.sort_index()

    # reorder columns
    column_order = ['latitude', 'longitude'] + [col for col in merged.columns if col not in ['latitude', 'longitude']]
    merged = merged[column_order]

    # rename some columns
    rename_cols = {'depth_m': 'depth', 'temperature_degrees_c': 'temperature',
                   'pH_avg_25degC': 'pH', 'TA_avg': 'TA', 
                   'DIC_avg': 'DIC',}
    merged.rename(columns=rename_cols, inplace=True)

    # check the merged dataframe
    tnow = dt.datetime.now(dt.UTC).strftime('%Y%m%d')
    merged.to_csv(os.path.join(wsdir, 'output', 'csv', f'{tnow}_merged_dataframe_to_check.csv'))

    ds = merged.to_xarray()

    for variable in list(ds.data_vars):
        try:
            ds[variable].attrs = va[variable]
        except KeyError:
            continue

    encoding = dict()

    for k in ds.data_vars:
        if k in ['project', 'station_id', 'glider_trajectory', 'deployment_recovery']:
            encoding[k] = dict(zlib=False, dtype=object, _FillValue=None)
        elif k in ['cast', 'niskin']:
            encoding[k] = dict(zlib=True, dtype=np.int32, _FillValue=np.float32(-9999))
        else:
            encoding[k] = dict(zlib=True, dtype=np.float32, _FillValue=np.float32(-9999.0))

    # add the encoding for time so xarray exports the proper time
    encoding["time"] = dict(calendar="gregorian", zlib=False, _FillValue=None, dtype=np.double)

    ds = ds.assign_attrs(ga)

    ds.to_netcdf(savefile, encoding=encoding, format="netCDF4", engine="netcdf4")


if __name__ == '__main__':
    main()
