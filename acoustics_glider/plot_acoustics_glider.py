#!/usr/bin/env python

"""
Author: Lori Garzio on 8/10/2021
Last modified: 2/19/2025
Quickly plot xsections of glider data variables that will be sent to an archive
"""

import os
import xarray as xr
import numpy as np
import pandas as pd
import yaml
import cmocean as cmo
import matplotlib.pyplot as plt
import dataset_archiving.common as cf
import dataset_archiving.plotting as pf
plt.rcParams.update({'font.size': 13})


def main(fname):
    savedir = os.path.join(os.path.dirname(fname), 'plots')
    os.makedirs(savedir, exist_ok=True)

    ds = xr.open_dataset(fname)
    deploy = ds.attrs['deployment']

    t0str = pd.to_datetime(np.nanmin(ds.time)).strftime('%Y-%m-%dT%H:%M')
    t1str = pd.to_datetime(np.nanmax(ds.time)).strftime('%Y-%m-%dT%H:%M')

    root_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(root_dir)
    configdir = os.path.join(parent_dir, 'configs')

    with open(os.path.join(configdir, 'plot_vars.yml')) as f:
        plt_vars = yaml.safe_load(f)

    for pv, info in plt_vars.items():
        try:
            variable = ds[pv]
        except KeyError:
            continue

        # plot xsection
        if len(variable) > 1:
            fig, ax = plt.subplots(figsize=(12, 6))
            plt.subplots_adjust(left=0.1)
            figttl_xsection = f'{deploy} {variable.attrs['long_name']}\n{t0str} to {t1str}'
            clab = f'{variable.attrs['long_name']} ({variable.attrs['units']})'
            xargs = dict()
            xargs['clabel'] = clab
            xargs['title'] = figttl_xsection
            xargs['date_fmt'] = '%m-%d'
            xargs['grid'] = True
            xargs['cmap'] = info['cmap']
            pf.xsection(fig, ax, ds.time.values, ds.depth_interpolated.values, variable.values, **xargs)

            sfilename = f'{deploy}_xsection_{pv}.png'
            sfile = os.path.join(savedir, sfilename)
            plt.savefig(sfile, dpi=300)
            plt.close()


if __name__ == '__main__':
    ncfile = '/Users/garzio/Documents/gliderdata/ru39-20240429T1522/ncei_azfp/ru39-20240429T1522-delayed.nc'
    main(ncfile)
