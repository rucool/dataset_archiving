#! /usr/bin/env python

"""
Common functions
"""

import numpy as np
import xarray as xr
from erddapy import ERDDAP
from netCDF4 import default_fillvals


def apply_ctd_hysteresis_qc(dataset, qc_variety='suspect_failed', add_comment=False):
    '''
    Apply CTD hysteresis test to conductivity, temperature, salinity and density
    User specifies if suspect (3) and/or failed (4) QC variables are applied. Default is both
    Add an optional user comment
    dataset: xarray dataset
    qc_variety: specify if suspect (3) and/or failed (4) QC variables are applied
    options are 'suspect_failed' (default) or 'failed_only'
    add_comment: optional user comment to add to the data array 
    '''
    qcvars = [x for x in list(dataset.data_vars) if '_hysteresis_test' in x]
    for qv in qcvars:
        target_var = list([qv.split('_hysteresis_test')[0]])
        target_var.append('salinity')
        target_var.append('density')

        if qc_variety == 'suspect_failed':
            qc_idx = np.where(np.logical_or(dataset[qv].values == 3, dataset[qv].values == 4))[0]
        elif qc_variety == 'failed_only':
            qc_idx = np.where(dataset[qv].values == 4)[0]
        else:
            raise(ValueError(f'Invalid qc_variety provided: {qc_variety}. Valid options are "suspect_failed" or "failed_only"'))

        for tv in target_var:
            # update comment to indicate that QC was applied
            if add_comment:
                if not hasattr(dataset[tv], 'comment'):
                    dataset[tv].attrs['comment'] = add_comment
                else:
                    if add_comment not in dataset[tv].attrs['comment']:
                        dataset[tv].attrs['comment'] = ' '.join((dataset[tv].comment, add_comment))
            # remove flagged values
            if len(qc_idx) > 0:
                dataset[tv][qc_idx] = np.nan


def apply_qartod_qc(dataset, qc_variety='suspect_failed', add_comment=False):
    '''
    Apply QARTOD summary QC to all variables except pressure
    Conductivity and temperature QC is applied to salinity and density
    User specifies if suspect (3) and/or failed (4) QC variables are applied. Default is both
    Add an optional user comment
    dataset: xarray dataset
    qc_variety: specify if suspect (3) and/or failed (4) QC variables are applied
    options are 'suspect_failed' (default) or 'failed_only'
    add_comment: optional user comment to add to the data array 
    '''
    qcvars = [x for x in list(dataset.data_vars) if '_qartod_summary_flag' in x]
    for qv in qcvars:
        if 'pressure' in qv:
            continue
        target_var = list([qv.split('_qartod_summary_flag')[0]])
        if target_var[0] in ['conductivity', 'temperature']:
            target_var.append('salinity')
            target_var.append('density')
        
        if qc_variety == 'suspect_failed':
            qc_idx = np.where(np.logical_or(dataset[qv].values == 3, dataset[qv].values == 4))[0]
        elif qc_variety == 'failed_only':
            qc_idx = np.where(dataset[qv].values == 4)[0]
        else:
            raise(ValueError(f'Invalid qc_variety provided: {qc_variety}. Valid options are "suspect_failed" or "failed_only"'))

        for tv in target_var:
            try:
                dataset[tv]
            except KeyError:
                continue
            # update comment to indicate that QC was applied
            if add_comment:
                if not hasattr(dataset[tv], 'comment'):
                    dataset[tv].attrs['comment'] = add_comment
                else:
                    if add_comment not in dataset[tv].attrs['comment']:
                        dataset[tv].attrs['comment'] = ' '.join((dataset[tv].comment, add_comment))
            # remove flagged values
            if len(qc_idx) > 0:
                dataset[tv][qc_idx] = np.nan


def get_dataset_variables(server, dataset_id):
    e = ERDDAP(server=server,
               protocol='tabledap',
               response='nc')
    var_dict = e._get_variables(dataset_id=dataset_id)

    return list(var_dict.keys())


def interpolate_depth(dataset):
    '''
    Interpolate depth variable in an xarray dataset.
    This function applies QARTOD QC to the depth variable, converts any failed (4) QC flags to NaN,
    and then performs linear interpolation on the depth values using pandas.DataFrame.interpolate.
    The interpolated depth is added to the dataset as a new DataArray named 'depth_interpolated'.
    dataset: xarray dataset containing a 'depth' variable
    '''
    
    # apply pressure QARTOD QC to depth. convert fail (4) QC flags to nan
    depthcopy = dataset.depth.copy()
    for qv in [x for x in dataset.data_vars if 'pressure_qartod' in x]:
        qv_vals = dataset[qv].values
        qv_idx = np.where(qv_vals == 4)[0]
        depthcopy[qv_idx] = np.nan
    
    # interpolate depth
    df = depthcopy.to_dataframe()
    # Drop the duplicate 'depth' column if it exists
    df = df.loc[:, ~df.columns.duplicated()]
    depth_interp = df['depth'].interpolate(method='linear', limit_direction='both', limit=2).values

    attrs = dataset.depth.attrs.copy()
    attrs['ancillary_variables'] = f'{attrs["ancillary_variables"]} depth'
    attrs['comment'] = f'Linear interpolated depth using pandas.DataFrame.interpolate'
    attrs['long_name'] = 'Interpolated Depth'
    attrs['source_sensor'] = 'depth'
    attrs['standard_name'] = 'depth'

    da = xr.DataArray(depth_interp.astype(dataset.depth.dtype), coords=dataset.depth.coords, 
                      dims=dataset.depth.dims, name='depth_interpolated', attrs=attrs)

    # use the encoding from the original depth variable
    set_encoding(da, original_encoding=dataset.depth.encoding)

    dataset['depth_interpolated'] = da


def return_erddap_nc(server, ds_id, variables=None, constraints=None):
    e = ERDDAP(server=server,
               protocol='tabledap',
               response='nc')
                      
    e.dataset_id = ds_id
    if constraints:
        e.constraints = constraints
    if variables:
        e.variables = variables
    
    ds = e.to_xarray(requests_kwargs={"timeout": 600})  # increase timeout to 10 minutes
    ds = ds.sortby(ds.time)
    return ds


def set_encoding(data_array, original_encoding=None):
    """
    Define encoding for a data array, using the original encoding from another variable (if applicable)
    :param data_array: data array to which encoding is added
    :param original_encoding: optional encoding dictionary from the parent variable
    (e.g. use the encoding from "depth" for the new depth_interpolated variable)
    """
    if original_encoding:
        data_array.encoding = original_encoding

    try:
        encoding_dtype = data_array.encoding['dtype']
    except KeyError:
        data_array.encoding['dtype'] = data_array.dtype

    try:
        encoding_fillvalue = data_array.encoding['_FillValue']
    except KeyError:
        # set the fill value using netCDF4.default_fillvals
        data_type = f'{data_array.dtype.kind}{data_array.dtype.itemsize}'
        data_array.encoding['_FillValue'] = default_fillvals[data_type]