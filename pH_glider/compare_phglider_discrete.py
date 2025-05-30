#!/usr/bin/env python

"""
Author: Lori Garzio on 5/9/2025
Last modified: 5/30/2025
Compare glider data to discrete water samples collected during glider deployment/recovery
1. Grab the first(last) 10 glider profiles at the beginning(end) of the deployment
2. Calculate the time and distance between the glider and discrete water sample
3. Plot the glider profiles and discrete water samples
4. Calculate the differences between the water samples and glider data. For surface water samples
(e.g. depth < 4 m), compare to the median of the glider data from 0-4m. For water samples >4 m depth,
compare to the median of the glider data from the water sample depth +/- 1 m.
5. Save the plots and summary data to a csv file
"""

import numpy as np
import pandas as pd
import xarray as xr
import os
import math
import gsw
import pytz
from erddapy import ERDDAP
import PyCO2SYS as pyco2
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size': 12})
pd.set_option('display.width', 320, "display.max_columns", 15)  # for display in pycharm console


def haversine(lat1, lon1, lat2, lon2):
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371000  # Radius of Earth in meters
    return c * r


def main(fname, proj):
    save_dir = os.path.join(os.path.dirname(fname), 'compare_glider_discrete')
    os.makedirs(save_dir, exist_ok=True)

    summary_headers = ['deployment_recovery', 'glider_date', 'discrete_date', 'collection_method', 'glider_n', 'discrete_n', 'time_difference_minutes',
                       'glider_depth_m', 'discrete_depth_m', 'glider_lon', 'glider_lat',
                       'discrete_lon', 'discrete_lat', 'distance_m', 'glider_ph', 'glider_ph_std', 'discrete_ph', 'discrete_ph_std', 'diff_ph',
                       'glider_ta', 'glider_ta_std', 'discrete_ta', 'discrete_ta_std', 'diff_ta', 'glider_temp', 'glider_temp_std', 'discrete_temp', 
                       'discrete_temp_std', 'glider_sal', 'glider_sal_std', 'discrete_sal', 'discrete_sal_std']
    summary_rows = []

    # grab water sampling dataset from ERDDAP
    server = 'https://rucool-sampling.marine.rutgers.edu/erddap'
    e = ERDDAP(server=server,
               protocol='tabledap',
               response='csv')
    e.dataset_id = 'pH_glider_carb_chem_water_sampling'
    df = e.to_pandas()
    
    # Remove units from column names
    df.columns = [col.split(' (')[0] for col in df.columns]

    # drop rows without pH
    df = df.dropna(axis=0, how='all', subset=['pH'])

    ds = xr.open_dataset(fname)
    ds = ds.swap_dims({'time': 'profile_time'})
    ds = ds.sortby(ds.profile_time)
    filename = fname.split('/')[-1]
    deploy = f'{filename.split("-")[0]}-{filename.split("-")[1]}'

    # subset the dataframe for the glider deployment (some rows are associated with multiple glider deployments)
    df2 = df.loc[df['glider_trajectory'].str.contains(deploy, na=False)]

    plt_vars = ['chlorophyll_a', 'pH', 'salinity', 'temperature', 'total_alkalinity']
    for dr in np.unique(df2['deployment_recovery']):
        df_dr = df2.loc[df2['deployment_recovery'] == dr]
        sample_time = np.nanmin(df_dr['time'])
        sample_lat = np.unique(df_dr['latitude'])
        sample_lon = np.unique(df_dr['longitude'])
        collection_method = np.unique(df_dr.collection_method).tolist()

        # discrete water sample metadata
        tsave = pd.to_datetime(sample_time).strftime('%Y%m%dT%H%M')
        slat = np.round(sample_lat[0], 4)
        slon = np.round(sample_lon[0], 4)
        sample_meta = f'Sample: {sample_time}, location {[str(slat), str(slon)]}'

        # subset glider data (10 profiles) at the beginning or end of the deployment
        n = 10
        profiletimes = np.unique(ds.profile_time.values)
        if dr == 'deployment':
            ptimes = profiletimes[0:n]
        elif dr == 'recovery':
            ptimes = profiletimes[-n:]
        
        dss = ds.sel(profile_time=slice(np.nanmin(ptimes), np.nanmax(ptimes)))
        
        # if there's barely any pH data, grab the next(previous) 10 profiles
        if np.sum(~np.isnan(dss.pH)) < 50:
            if dr == 'deployment':
                ptimes = profiletimes[n:n + 10]
            elif dr == 'recovery':
                ptimes = profiletimes[-n - 10:-n]
            dss = ds.sel(profile_time=slice(np.nanmin(ptimes), np.nanmax(ptimes)))

        dss_t0 = pd.to_datetime(np.nanmin(dss.time.values))
        dss_t1 = pd.to_datetime(np.nanmax(dss.time.values))

        # glider metadata
        dss_t0str = pd.to_datetime(dss_t0).strftime('%Y-%m-%dT%H:%M')
        dss_t1str = pd.to_datetime(dss_t1).strftime('%Y-%m-%dT%H:%M')
        dss_t0savestr = pd.to_datetime(dss_t0).strftime('%Y%m%dT%H%M')
        dss_t1savestr = pd.to_datetime(dss_t1).strftime('%Y%m%dT%H%M')
        glat = np.round(np.nanmean(dss.profile_lat.values), 4)
        glon = np.round(np.nanmean(dss.profile_lon.values), 4)
        glider_meta = f'Glider profiles: {dss_t0str} to {dss_t1str},\nlocation {[str(glat), str(glon)]}'

        # differences between glider and samples - distance and time
        distance_meters = int(haversine(glat, glon, slat, slon))
        diff_mins = int(np.round(abs(pytz.UTC.localize(dss_t0) - pd.to_datetime(sample_time)).total_seconds() / 60))
        diff_meta = f'Distance: {distance_meters} meters'

        for pv in plt_vars:
            # get the discrete water sample data
            sample_depth = df_dr['depth']
            if pv == 'pH':
                sample = df_dr['pH_corrected']
            elif pv == 'salinity':
                sample = df_dr['salinity']
            elif pv == 'temperature':
                sample = df_dr['temperature']
            elif pv == 'chlorophyll_a':
                sample = np.repeat(np.nan, len(sample_depth))
            elif pv == 'total_alkalinity':
                sample = df_dr['TA']

            fig, ax = plt.subplots(figsize=(8, 10))

            # plot glider data
            ax.scatter(dss[pv], dss.depth_interpolated, c='tab:blue', s=20, label=f'glider {pv}')

            if pv != 'chlorophyll_a':
                # plot water sample data
                ax.scatter(sample.astype(float), sample_depth.astype(float), c='tab:red', ec='k', s=50,
                            label='water samples')

            ax.legend()
            #plt.ylim(0, 16)
            #plt.xlim(xlims)
            ax.set_xlabel(pv)
            ax.invert_yaxis()
            ax.set_ylabel('Depth (m)')
            ax.set_title(f'Glider {dr.capitalize()}\n{sample_meta}\n{glider_meta}\n{diff_meta}, Collection: {collection_method}')

            sfilename = f'{deploy}_discrete_comparison_{dr}_{dss_t0savestr}-{dss_t1savestr}_{pv}.png'
            sfile = os.path.join(save_dir, sfilename)
            plt.savefig(sfile, dpi=300)
            plt.close()

        # write summary file
        df_dr.loc[df_dr['depth'] <= 2, 'depth'] = 2  # set depth to 2 m for shallow samples

        # round discrete depth up to the nearest multiple of 2
        df_dr['depth_ceil'] = np.ceil(df_dr['depth'] / 2) * 2

        for depth_bin, group in df_dr.groupby('depth_ceil'):
            discrete_n = len(group)
            if discrete_n == 0:
                continue
            coll_method = np.unique(group.collection_method).tolist()
            discrete_depth = np.nanmedian(group.depth)
            if discrete_depth < 4:
                gl_depth_idx = np.where(dss.depth_interpolated < 4)[0]
            else:
                depth1 = discrete_depth - 1
                depth2 = discrete_depth + 1
                gl_depth_idx = np.where(np.logical_and(dss.depth_interpolated > depth1,
                                                       dss.depth_interpolated < depth2))[0]
            try:
                gl_depth = int(np.round(np.nanmedian(dss.depth_interpolated[gl_depth_idx])))
            except ValueError:
                print('gl_depth = NaN')
                gl_depth = np.nan

            glider_n = int(np.sum(~np.isnan(dss.pH[gl_depth_idx])))
            discrete_ph = np.round(np.nanmedian(group.pH_corrected), 3)
            dph_std = np.round(np.nanstd(group.pH_corrected), 3)
            #glider_ph = np.round(np.nanmedian(dss.ph_total_shifted[gl_depth_idx]), 3)
            glider_ph = np.round(np.nanmedian(dss.pH[gl_depth_idx]), 3)
            gph_std = np.round(np.nanstd(dss.pH[gl_depth_idx]), 3)
            ph_diff = np.round(glider_ph - discrete_ph, 3)
            discrete_ta = int(np.round(np.nanmedian(group.TA)))
            dta_std = int(np.round(np.nanstd(group.TA)))
            try:
                glider_ta = int(np.round(np.nanmedian(dss.total_alkalinity[gl_depth_idx])))
                gta_std = int(np.round(np.nanstd(dss.total_alkalinity[gl_depth_idx])))
            except ValueError:
                print('glider_ta = NaN')
                glider_ta = np.nan
                gta_std = np.nan
            ta_diff = np.round(glider_ta - discrete_ta, 3)
            discrete_temp = np.round(np.nanmedian(group.temperature), 1)
            dtemp_std = np.round(np.nanstd(group.temperature), 1)
            glider_temp = np.round(np.nanmedian(dss.temperature[gl_depth_idx]), 1)
            gtemp_std = np.round(np.nanstd(dss.temperature[gl_depth_idx]), 1)
            discrete_sal = np.round(np.nanmedian(group.salinity), 2)
            dsal_std = np.round(np.nanstd(group.salinity), 2)
            glider_sal = np.round(np.nanmedian(dss.salinity[gl_depth_idx]), 2)
            gsal_std = np.round(np.nanstd(dss.salinity[gl_depth_idx]), 2)

            summary_data = [dr, dss_t0str, sample_time, coll_method, glider_n, discrete_n, diff_mins, gl_depth, discrete_depth, 
                            glon, glat, slon, slat, distance_meters, glider_ph, gph_std, discrete_ph, dph_std, ph_diff, 
                            glider_ta, gta_std, discrete_ta, dta_std, ta_diff, glider_temp, gtemp_std, discrete_temp, dtemp_std, 
                            glider_sal, gsal_std, discrete_sal, dsal_std]

            summary_rows.append(summary_data)

    summary_df = pd.DataFrame(summary_rows, columns=summary_headers)
    summary_df.sort_values(by=['discrete_date', 'discrete_depth_m'], inplace=True)

    # save the summary file to the local directory with the plots
    summary_df.to_csv(os.path.join(save_dir, f'{deploy}_groundtruthing_table.csv'), index=False)

    # also save the summary file to a common location for each project to combine and share via ERDDAP
    currentdir = os.path.dirname(os.path.abspath(__file__))
    sfile = os.path.join(currentdir, 'groundtruthing_tables', proj, f'{deploy}_groundtruthing_table.csv')
    summary_df.to_csv(sfile, index=False)


if __name__ == '__main__':
    ncfile = '/Users/garzio/Documents/rucool/Saba/gliderdata/2023/ru39-20231018T1426/ncei_pH/ru39-20231018T1426-delayed.nc'
    project = 'RMI'
    main(ncfile, project)
