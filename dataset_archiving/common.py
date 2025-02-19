#! /usr/bin/env python

"""
Common functions
"""

import numpy as np
from erddapy import ERDDAP


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


def return_erddap_nc(server, ds_id, variables=None, constraints=None):
    variables = variables or None
    constraints = constraints or None

    e = ERDDAP(server=server,
               protocol='tabledap',
               response='nc')
    e.dataset_id = ds_id
    if constraints:
        e.constraints = constraints
    if variables:
        e.variables = variables
    
    kwargs = dict()
    kwargs['timeout'] = 600  # this isn't working

    ds = e.to_xarray(**kwargs)
    ds = e.to_xarray()
    ds = ds.sortby(ds.time)
    return ds
