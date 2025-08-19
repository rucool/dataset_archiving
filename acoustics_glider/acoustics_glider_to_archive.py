#!/usr/bin/env python

"""
Author: Lori Garzio on 2/19/2025
Last modified: 8/19/2025
Process final acoustics glider datasets to archive:
AZFP to NCEI (https://www.ncei.noaa.gov/products/water-column-sonar-data)
DMON to NCEI (https://www.ncei.noaa.gov/products/passive-acoustic-data)
Note: if there is a pH sensor on the glider (likely AZFP glider), sometimes the first few pH profiles 
are bad due to the sensor acclimating or bubbles that need to work themselves out. Need
to first determine if this is the case (see pH_glider/plot_phglider_first_profiles.py).
Then enter the number of pH profiles to remove from the dataset in the arguments to this script
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


def main(fname, acoustics, rfp):
    savedir = os.path.join(os.path.dirname(fname), f'ncei_{acoustics}')
    os.makedirs(savedir, exist_ok=True)

    ds = xr.open_dataset(fname)
    try:
        deploy = ds.attrs['deployment']
    except KeyError:
        deploy = fname.split('/')[-1].split('-profile')[0]  # if no deployment in attrs, use the filename

    # grab profile_id encoding
    pid_encoding = ds.profile_id.encoding

    ds = ds.drop_vars(names=['profile_id', 'rowSize', 'trajectory', 'trajectoryIndex'])
    ds = ds.swap_dims({'obs': 'time'})
    ds = ds.sortby(ds.time)

    comment = 'Data flagged by QC tests (suspect and fail) were removed.'

    # apply QARTOD QC to all variables except pressure
    kwargs = dict()
    kwargs['add_comment'] = comment
    #kwargs['qc_variety'] = 'failed_only'  # suspect_failed (default) or failed_only
    cf.apply_qartod_qc(ds, **kwargs)

    # apply CTD hysteresis test QC
    cf.apply_ctd_hysteresis_qc(ds, **kwargs)

    # apply pH QC
    try:
        ds['pH'].attrs['comment'] = ' '.join((ds['pH'].comment, comment))
        qcvars = [x for x in list(ds.data_vars) if 'pH_qartod_' in x]
        for qv in qcvars:
            qc_idx = np.where(np.logical_or(ds[qv].values == 3, ds[qv].values == 4))[0]
            if len(qc_idx) > 0:
                ds['pH'][qc_idx] = np.nan

        # there's a lot of noise in pH at the surface, so set pH/TA/omega values to nan when depth_interpolated < 1 m
        add_comment = 'Values at depths < 1m were removed due to noise typically observed at the surface'
        oavars = ['pH', 'aragonite_saturation_state', 'total_alkalinity']
        idx = np.where(ds.depth_interpolated < 1)[0]
        for oav in oavars:
            ds[oav].values[idx] = np.nan
            ds[oav].attrs['comment'] = ' '.join((ds[oav].comment, add_comment))

        # remove first n pH/TA/omega profiles (bad/suspect data when the sensor was equilibrating)
        if np.logical_and(isinstance(rfp, int), rfp > 0):
            add_comment = f'First {rfp} profiles removed due to bad/suspect data when the sensor was equilibrating.'
            profiletimes = np.unique(ds.profile_time.values)
            ptimes = profiletimes[0:rfp]
            pidx = np.where(np.isin(ds.profile_time.values, ptimes))[0]
            for oav in oavars:
                ds[oav].values[pidx] = np.nan
                ds[oav].attrs['comment'] = ' '.join((ds[oav].comment, add_comment))
    except KeyError:
        pass

    # remove clearly bad data (usually from older datasets that don't have QC)
    idx = np.where(ds.conductivity <= 0)[0]
    ctdvars = ['conductivity', 'temperature', 'salinity', 'density']
    for cv in ctdvars:
        ds[cv].values[idx] = np.nan
    
    try:
        idx = np.where(ds.oxygen_concentration <= 0)[0]
        oxyvars = ['oxygen_concentration', 'oxygen_saturation']
        for ov in oxyvars:
            ds[ov].values[idx] = np.nan
    except AttributeError:
        pass
    
    # fix pressure units
    if ds.pressure.units == 'bar':
        if 'multiplied by 10 to convert from bar to dbar' in ds.pressure.comment:
            ds.pressure.attrs['units'] = 'dbar'

    # fix depth_interpolated standard_name and units
    # or calculate depth_interpolated if it's not available in the file
    try:
        ds.depth_interpolated.attrs['standard_name'] = 'depth'
        ds.depth_interpolated.attrs['units'] = 'm'
    except AttributeError:
        # interpolate depth
        cf.interpolate_depth(ds)
        ds.depth_interpolated.attrs['standard_name'] = 'depth'
        ds.depth_interpolated.attrs['units'] = 'm'

    # drop extra variables
    drop_vars = []
    search_str = ['_hysteresis_test', '_qartod_', '_optimal_shift', 'ctd41cp_timestamp', 'water_depth']
    for ss in search_str:
        append_vars = [x for x in ds.data_vars if ss in x]
        drop_vars.append(append_vars)

    drop_vars = [x for xs in drop_vars for x in xs]
    ds = ds.drop_vars(drop_vars)

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

    # update global attrs using the sensor_glider_attrs.yml config file
    root_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(root_dir)
    configdir = os.path.join(parent_dir, 'configs')

    with open(os.path.join(configdir, f'{acoustics}_glider_attrs.yml')) as f:
        add_attrs = yaml.safe_load(f)

    ds.attrs['processing_level'] = add_attrs['processing_level']

    tnow = dt.datetime.now(dt.UTC).strftime('%Y-%m-%dT%H:%M:00Z')
    ds.attrs['date_modified'] = tnow

    ds.attrs['references'] = ', '.join((ds.attrs['references'], add_attrs['references']))

    # save final .nc file
    savefile = os.path.join(savedir, f'{deploy}-delayed.nc')
    ds.to_netcdf(savefile, format="netCDF4", engine="netcdf4", unlimited_dims=["time"])

    # file to test formatting in IOOS compliance checker https://compliance.ioos.us/index.html
    sfile = os.path.join(savedir, f'{deploy}-delayed-test.nc')
    newds = ds.isel(time=slice(0, 100))
    newds.to_netcdf(sfile, format="netCDF4", engine="netcdf4", unlimited_dims=["time"])

    # print variable names in file to double check
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
    rownames = ['start', 'end', 'program', 'project', 'sea_name', 'summary']
    
    values = [pd.to_datetime(np.nanmin(ds.time.values)).strftime('%Y-%m-%d'),
              pd.to_datetime(np.nanmax(ds.time.values)).strftime('%Y-%m-%d'),
              ds.attrs['program'],
              ds.attrs['project'],
              ds.attrs['sea_name'],
              ds.attrs['summary']]
    
    vardict = dict(name = rownames,
                   value = values)
    dfmeta = pd.DataFrame(vardict)
    dfmeta.to_csv(os.path.join(savedir, f'deployment_metadata-{deploy}.csv'), index=False)

    # print instrument metadata to csv
    instrument_vars = [x for x in list(ds.data_vars) if 'instrument_' in x]

    vardict = dict(name = instrument_vars,
                   maker = [],
                   model = [],
                   sn = [],
                   cal_date = [],
                   calibration_coeffs = []
                   )

    for iv in instrument_vars:
        try:
            vardict['maker'].append(ds[iv].attrs["maker"])
            vardict['model'].append(ds[iv].attrs["model"])
        except KeyError:
            vardict['maker'].append(ds[iv].attrs["make_model"])
            vardict['model'].append(ds[iv].attrs["make_model"])
        vardict['sn'].append(ds[iv].attrs["serial_number"])
        vardict['cal_date'].append(ds[iv].attrs["calibration_date"])
        try:
            vardict['calibration_coeffs'].append(ds[iv].attrs["calibration_coefficients"])
        except KeyError:
            vardict['calibration_coeffs'].append('')    
    
    dfmeta = pd.DataFrame(vardict)
    dfmeta.to_csv(os.path.join(savedir, f'instrument_metadata-{deploy}.csv'), index=False)
    

if __name__ == '__main__':
    ncfile = '/Users/garzio/Documents/gliderdata/ru40-20241021T1654/ru40-20241021T1654-profile-sci-delayed.nc'
    acoustics = 'dmon'  # 'azfp' or 'dmon'
    remove_first_profiles = False  # remove the first 10-12 pH profiles? # of profiles to remove or False
    main(ncfile, acoustics, remove_first_profiles)
