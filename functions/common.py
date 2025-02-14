#! /usr/bin/env python

"""
Common functions
"""

from erddapy import ERDDAP

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
    ds = e.to_xarray()
    ds = ds.sortby(ds.time)
    return ds
