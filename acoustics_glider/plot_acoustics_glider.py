#!/usr/bin/env python

"""
Author: Lori Garzio on 8/10/2021
Last modified: 5/13/2025
Quickly plot xsections of glider data variables that will be sent to an archive
Also plot the first 30 pH profiles to make sure the bad data (when the sensor was equilibrating) are removed.
"""

import os
import xarray as xr
import numpy as np
import pandas as pd
import yaml
import cmocean as cmo
import cool_maps.plot as cplt
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import dataset_archiving.common as cf
import dataset_archiving.plotting as pf
plt.rcParams.update({'font.size': 13})


def main(fname):
    savedir = os.path.join(os.path.dirname(fname), 'plots')
    os.makedirs(savedir, exist_ok=True)

    ds = xr.open_dataset(fname)
    ds = ds.swap_dims({'time': 'profile_time'})  # for plotting pH profiles
    try:
        deploy = ds.attrs['deployment']
    except KeyError:
        f = fname.split('/')[-1]
        deploy = f'{f.split("-")[0]}-{f.split("-")[1]}'  # get the deployment from the filename

    t0str = pd.to_datetime(np.nanmin(ds.time)).strftime('%Y-%m-%dT%H:%M')
    t1str = pd.to_datetime(np.nanmax(ds.time)).strftime('%Y-%m-%dT%H:%M')

    # make a map of the glider track
    # define the map extent
    df = pd.DataFrame({'lon': ds.profile_lon.values, 'lat': ds.profile_lat.values})
    df = df.drop_duplicates()
    extent = [np.nanmin(df.lon) - 1.5, np.nanmax(df.lon) + 1.5,
              np.nanmin(df.lat) - 1, np.nanmax(df.lat) + 1]
    
    kwargs = dict()
    kwargs['coast'] = 'high'
    kwargs['oceancolor'] = 'none'
    kwargs['decimal_degrees'] = True
    kwargs['bathymetry'] = True
    #kwargs['bathymetry_file'] = '/Users/garzio/Documents/rucool/bathymetry/GEBCO_2014_2D_-100.0_0.0_-10.0_50.0.nc'
    kwargs['bathymetry_method'] = 'topo_log'
    fig, ax = cplt.create(extent, **kwargs)

    ax.scatter(df.lon, df.lat, color='magenta', marker='.', s=20, transform=ccrs.PlateCarree(), zorder=10)
    
    plt.title(f'{deploy}')
    sfilename = f'{deploy}_glider_track.png'
    sfile = os.path.join(savedir, sfilename)
    plt.savefig(sfile, dpi=200)
    plt.close()

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

            # plot first 30 pH profiles
            if pv == 'pH':  # pH pH_corrected
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
    ncfile = '/Users/garzio/Documents/gliderdata/ru39-20240429T1522/ncei_azfp/ru39-20240429T1522-delayed.nc'
    main(ncfile)
