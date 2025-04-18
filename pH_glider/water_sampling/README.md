# pH glider water sampling

Author: Lori Garzio _lgarzio@marine.rutgers.edu_

Tools for formatting water sampling data to share via [ERDDAP](https://rucool-sampling.marine.rutgers.edu/erddap/index.html).

## Instructions

1. Update the [source .csv files](https://github.com/rucool/dataset_archiving/tree/master/pH_glider/water_sampling/files) with most recent data.

2. Update the [config files](https://github.com/rucool/dataset_archiving/tree/master/pH_glider/water_sampling/config) if necessary (if there is new project metadata to include, etc)

2. Run [ph_watersampling_to_erddap](https://github.com/rucool/dataset_archiving/blob/master/pH_glider/water_sampling/ph_watersampling_to_erddap.py) to combine the pH, TA, and DIC values onto one row of data per sample (two sample bottles are required for the analysis so the data are recorded on two separate lines for the same sample.) This exports a .csv file of the merged dataset to manually check, and a formatted NetCDF file for sharing via ERDDAP.

3. Check the new lines added in the [merged csv file](https://github.com/rucool/dataset_archiving/tree/master/pH_glider/water_sampling/output/csv) for any empty cells. This most often occurs when there are small typos in the source data files (e.g. temperature might be slightly different for two sample bottles that were taken at the same time/location). If necessary, fix these typos in the source files and re-run [ph_watersampling_to_erddap](https://github.com/rucool/dataset_archiving/blob/master/pH_glider/water_sampling/ph_watersampling_to_erddap.py).

4. Share [output](https://github.com/rucool/dataset_archiving/tree/master/pH_glider/water_sampling/output) NetCDF file via [ERDDAP](https://rucool-sampling.marine.rutgers.edu/erddap/index.html).
