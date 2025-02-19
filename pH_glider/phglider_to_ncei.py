#!/usr/bin/env python

"""
Author: Lori Garzio on 4/28/2021
Last modified: 2/19/2025
Process final pH glider dataset to upload to the NCEI OA data portal
(https://www.ncei.noaa.gov/access/ocean-carbon-acidification-data-system-portal/)
"""

import os
import numpy as np
import pandas as pd
import xarray as xr
import datetime as dt
import yaml
import dataset_archiving.common as cf


def delete_attrs(da):
    for item in ['actual_range', 'ancillary_variables']:
        try:
            del da.attrs[item]
        except KeyError:
            continue


def main(fname):
    savedir = os.path.join(os.path.dirname(fname), 'ncei_pH')
    os.makedirs(savedir, exist_ok=True)

    ds = xr.open_dataset(fname)
    deploy = ds.attrs['deployment']

    # grab profile_id encoding
    pid_encoding = ds.profile_id.encoding

    ds = ds.drop_vars(names=['profile_id', 'rowSize', 'trajectory', 'trajectoryIndex'])
    ds = ds.swap_dims({'obs': 'time'})
    ds = ds.sortby(ds.time)

    comment = 'Data flagged by QC tests (suspect and fail) were removed.'

    # apply QARTOD QC to all variables except pressure
    kwargs = dict()
    kwargs['add_comment'] = comment
    cf.apply_qartod_qc(ds, **kwargs)

    # apply CTD hysteresis test QC
    cf.apply_ctd_hysteresis_qc(ds, **kwargs)

    # apply pH QC
    ds['pH'].attrs['comment'] = ' '.join((ds['pH'].comment, comment))
    qcvars = [x for x in list(ds.data_vars) if 'pH_qartod_' in x]
    for qv in qcvars:
        qc_idx = np.where(np.logical_or(ds[qv].values == 3, ds[qv].values == 4))[0]
        if len(qc_idx) > 0:
            ds['pH'][qc_idx] = np.nan

    # drop extra variables
    drop_vars = []
    search_str = ['_hysteresis_test', '_qartod_', '_optimal_shift', 'ctd41cp_timestamp', 'water_depth',
                  'm_pitch', 'm_roll']
    for ss in search_str:
        append_vars = [x for x in ds.data_vars if ss in x]
        drop_vars.append(append_vars)

    drop_vars = [x for xs in drop_vars for x in xs]
    ds = ds.drop_vars(drop_vars)

    # there's a lot of noise in pH at the surface, so set pH/TA/omega values to nan when depth_interpolated < 1 m
    add_comment = 'Values at depths < 1m were removed due to noise typically observed at the surface'
    oavars = ['pH', 'aragonite_saturation_state', 'total_alkalinity']
    idx = np.where(ds.depth_interpolated < 1)[0]
    for oav in oavars:
        ds[oav].values[idx] = np.nan
        ds[oav].attrs['comment'] = ' '.join((ds[oav].comment, add_comment))

    # add profile_id
    attributes = dict(
        ancillary_variables='profile_time',
        cf_role='profile_id',
        comment='Unique identifier of the profile. The profile ID is the mean profile timestamp.',
        ioos_category='Identifier',
        long_name='Profile ID'
    )
    name = 'profile_id'
    pid = ds.profile_time.values.astype('datetime64[s]').astype('int')
    da = xr.DataArray(pid, coords=ds.profile_time.coords, dims=ds.profile_time.dims, name=name, attrs=attributes)
    ds[name] = da
    ds[name].encoding = pid_encoding

    # fix pressure units
    if ds.pressure.units == 'bar':
        if 'multiplied by 10 to convert from bar to dbar' in ds.pressure.comment:
            ds.pressure.attrs['units'] = 'dbar'

    # fix depth_interpolated standard_name and units
    ds.depth_interpolated.attrs['standard_name'] = 'depth'
    ds.depth_interpolated.attrs['units'] = 'm'

    # make sure valid_min and valid_max are the same data type as the variables
    for v in ds.data_vars:
        try:
            ds[v].attrs['valid_min'] = np.float32(ds[v].valid_min)
            ds[v].attrs['valid_max'] = np.float32(ds[v].valid_max)
        except AttributeError:
            continue

    # delete some variable attributes
    for v in ds.data_vars:
        delete_attrs(ds[v])

    for v in ds.coords:
        delete_attrs(ds[v])

    # update global attrs using the phglider_attrs.yml config file
    root_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(root_dir)
    configdir = os.path.join(parent_dir, 'configs')

    with open(os.path.join(configdir, 'phglider_attrs.yml')) as f:
        phglider_attrs = yaml.safe_load(f)

    ds.attrs['processing_level'] = phglider_attrs['processing_level']

    tnow = dt.datetime.now(dt.UTC).strftime('%Y-%m-%dT%H:%M:00Z')
    ds.attrs['date_modified'] = tnow

    ds.attrs['references'] = ', '.join((ds.attrs['references'], phglider_attrs['references']))

    # export unique lonlat.csv file NCEI data submission
    lonlat = dict(lon=list(np.round(ds.longitude.values, 4)),
                  lat=list(np.round(ds.latitude.values, 4)))
    df = pd.DataFrame(lonlat)
    df.drop_duplicates(inplace=True)

    df.to_csv(os.path.join(savedir, f'lonlat-{deploy}.csv'), header=None, index=None)

    # save final .nc file
    savefile = os.path.join(savedir, f'{deploy}-delayed.nc')
    ds.to_netcdf(savefile, format="netCDF4", engine="netcdf4", unlimited_dims=["time"])

    # file to test formatting in IOOS compliance checker https://compliance.ioos.us/index.html
    sfile = os.path.join(savedir, f'{deploy}-delayed-test.nc')
    newds = ds.isel(time=slice(0, 100))
    newds.to_netcdf(sfile, format="netCDF4", engine="netcdf4", unlimited_dims=["time"])

    # print variable information for NCEI metadata submission to csv
    vardict = dict()
    for v in list(ds.coords):
        try:
            units = ds[v].units
        except AttributeError:
            units = ''
        vardict[v] = dict(units=units,
                          long_name=ds[v].long_name)
    for v in list(ds.data_vars):
        try:
            units = ds[v].units
        except AttributeError:
            units = ''
        vardict[v] = dict(units=units,
                          long_name=ds[v].long_name)

    dfmeta = pd.DataFrame(vardict)
    dfmeta = dfmeta.transpose()
    dfmeta.to_csv(os.path.join(savedir, f'variables-{deploy}.csv'))

    # print deployment information for NCEI metadata submission to csv
    rownames = ['start', 'end', 'North Latitude Extent', 'South Latitude Extent', 'West Longitude Extent', 'East Longitude Extent', 'summary']
    north = np.round(np.nanmax(df.lat), 3)
    south = np.round(np.nanmin(df.lat), 3)
    west = np.round(np.nanmin(df.lon), 3)
    east = np.round(np.nanmax(df.lon), 3)
    
    values = [pd.to_datetime(np.nanmin(ds.time.values)).strftime('%Y-%m-%d'),
              pd.to_datetime(np.nanmax(ds.time.values)).strftime('%Y-%m-%d'),
              north,
              south,
              west,
              east,
              ds.attrs['summary']]
    
    vardict = dict(name = rownames,
                   value = values)
    dfmeta = pd.DataFrame(vardict)
    dfmeta.to_csv(os.path.join(savedir, f'deployment_metadata-{deploy}.csv'), index=False)

    # print instrument metadata to csv
    print('')
    print('instruments:')
    instrument_vars = [x for x in list(ds.data_vars) if 'instrument_' in x]

    vardict = dict(name = instrument_vars,
                   maker = [],
                   model = [],
                   sn = [],
                   cal_date = [],
                   calibration_coeffs = []
                   )

    for iv in instrument_vars:
        vardict['maker'].append(ds[iv].attrs["maker"])
        vardict['model'].append(ds[iv].attrs["model"])
        vardict['sn'].append(ds[iv].attrs["serial_number"])
        vardict['cal_date'].append(ds[iv].attrs["calibration_date"])
        try:
            vardict['calibration_coeffs'].append(ds[iv].attrs["calibration_coefficients"])
        except KeyError:
            vardict['calibration_coeffs'].append('')    
    
    dfmeta = pd.DataFrame(vardict)
    dfmeta.to_csv(os.path.join(savedir, f'instrument_metadata-{deploy}.csv'), index=False)
    

if __name__ == '__main__':
    ncfile = '/Users/garzio/Documents/gliderdata/ru39-20240429T1522/ru39-20240429T1522-profile-sci-delayed.nc'
    main(ncfile)
