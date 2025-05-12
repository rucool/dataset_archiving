# pH glider
A collection of tools to post-process and prepare datasets related to pH glider deployments for archiving at the National Centers for Environmental Information (NCEI) and in Rutgers ERDDAP server.

pH glider datasets are QC'd and archived in NCEI's [Ocean Carbon and Acidification Data System (OCADS)](https://www.ncei.noaa.gov/products/ocean-carbon-acidification-data-system).

## Post-processing Instructions

1. For each deployment, download glider .nc files to your local machine using [download_glider_dataset.py](https://github.com/rucool/dataset_archiving/blob/master/download_glider_dataset.py) (add_engineering_vars can be False)

2. Sometimes the first few profiles are bad due to the sensor acclimating or bubbles that need to work themselves out. Plot the first 30 profiles to determine if profiles need to be removed [plot_phglider_first_profiles.py](https://github.com/rucool/dataset_archiving/blob/master/pH_glider/plot_phglider_first_profiles.py). These profiles can be removed from the dataset in the next step.

3. [phglider_to_ncei.py](https://github.com/rucool/dataset_archiving/blob/master/pH_glider/phglider_to_ncei.py) Process final pH glider dataset to upload to the [NCEI OA data portal](https://www.ncei.noaa.gov/access/ocean-carbon-acidification-data-system-portal/)
    1. Apply QC
    2. Drop extra variables that we don't need to include in the archive
    3. Remove pH/TA/omega when depth_interpolated < 1 m (due to noise at surface)
    4. Optional: remove first n pH profiles (bad/suspect data when the sensor was equilibrating)
    5. Fix some historically incorrect metadata (if necessary)
    6. Add additional metadata specific to pH datasets
    7. Export a lonlat.csv file required for NCEI data submission
    8. Save the final netCDF file
    9. Print variable and deployment information to a csv file to help with NCEI submission

4. [plot_phglider_ncei.py](https://github.com/rucool/dataset_archiving/blob/master/pH_glider/plot_phglider_ncei.py): make quick plots of the glider data variables for a quick check before archiving.

5. Compare each glider deployment and recovery to the water sampling (in progress).

6. Submit the dataset in the OCADS submission data portal
