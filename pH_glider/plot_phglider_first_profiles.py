#!/usr/bin/env python

"""
Author: Lori Garzio on 5/5/2025
Last modified: 5/5/2025
Plot the first 30 pH profiles to determine if data needs to be removed.
Sometimes the first few profiles are bad due to the sensor acclimating or bubbles that need to work themselves out.
"""

import os
import xarray as xr
import numpy as np
import pandas as pd
import yaml
import matplotlib.pyplot as plt
import dataset_archiving.common as cf
import dataset_archiving.plotting as pf
plt.rcParams.update({'font.size': 13})


def main(fname):
    savedir = os.path.join(os.path.dirname(fname), 'first_profiles')
    os.makedirs(savedir, exist_ok=True)

    ds = xr.open_dataset(fname)
    try:
        deploy = ds.attrs['deployment']
    except KeyError:
        f = fname.split('/')[-1]
        deploy = f'{f.split("-")[0]}-{f.split("-")[1]}'  # get the deployment from the filename

    try:
        ds = ds.drop_vars(names=['profile_id', 'rowSize', 'trajectory', 'trajectoryIndex'])
    except ValueError:
        ds = ds.drop_vars(names=['profile_id', 'rowSize', 'trajectory'])
    ds = ds.swap_dims({'obs': 'profile_time'})
    ds = ds.sortby(ds.profile_time)

    ds['sbe41n_ph_ref_voltage'][ds['sbe41n_ph_ref_voltage'] == 0.0] = np.nan  # convert zeros to nan
    #ds['salinity'][ds['salinity'] < 28] = np.nan

    # grab the first 30 profiles and plot each variable
    n = 30
    profiletimes = np.unique(ds.profile_time.values)
    ptimes = profiletimes[0:n]
    colors = plt.cm.rainbow(np.linspace(0, 1, int(len(ptimes)/2)))
    colors = np.repeat(colors, 2, axis=0)  # repeat colors for each profile
    labels = ['0-1', '2-3', '4-5', '6-7', '8-9',
              '10-11', '12-13', '14-15', '16-17', '18-19',
              '20-21', '22-23', '24-25', '26-27', '28-29']
    labels = np.repeat(labels, 2, axis=0)  # repeat labels for each profile
    t0str = pd.to_datetime(np.nanmin(ptimes)).strftime('%Y-%m-%dT%H:%M')
    t1str = pd.to_datetime(np.nanmax(ptimes)).strftime('%Y-%m-%dT%H:%M')

    root_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(root_dir)
    configdir = os.path.join(parent_dir, 'configs')

    with open(os.path.join(configdir, 'plot_vars.yml')) as f:
        plt_vars = yaml.safe_load(f)

    plt_vars['sbe41n_ph_ref_voltage'] = {'cmap': 'cmo.matter'}  # add voltages

    for pv, info in plt_vars.items():
        try:
            variable = ds[pv]
        except KeyError:
            continue
    
        fig, ax = plt.subplots(figsize=(8, 10))
        for i, pt in enumerate(ptimes):
            ds_sel = ds.sel(profile_time=pt)
            df = pd.DataFrame({'depth': ds_sel['depth_interpolated'].values,
                            'pv': ds_sel[pv].values})
            df = df.dropna()
            ax.plot(df['pv'], df['depth'], lw=.75, color=colors[i], label=labels[i])
            ax.scatter(df['pv'], df['depth'], color=colors[i], s=5, edgecolor='None')
        
        ax.invert_yaxis()
        ax.set_ylabel('depth_interpolated')
        ax.set_xlabel(pv)
        ax.set_title(f'{deploy} first {n} {pv} profiles\n{t0str} to {t1str}')

        handles, labels = plt.gca().get_legend_handles_labels()  # only show one set of legend labels
        by_label = dict(zip(labels, handles))
        ax.legend(by_label.values(), by_label.keys(), framealpha=0.5, ncol=2, loc='best')

        sfilename = f'{deploy}_{pv}_first_{n}_profiles.png'
        sfile = os.path.join(savedir, sfilename)
        plt.savefig(sfile, dpi=300)
        plt.close()


if __name__ == '__main__':
    ncfile = '/Users/garzio/Documents/rucool/Saba/gliderdata/2023/ru39-20231103T1413/delayed/ru39-20231103T1413-profile-sci-delayed.nc'
    main(ncfile)
