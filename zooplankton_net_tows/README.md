# Zooplankton Net Tows

Author: Lori Garzio _lgarzio@marine.rutgers.edu_

Tools for formatting zooplankton net tow data to share via [ERDDAP](https://rucool-sampling.marine.rutgers.edu/erddap/index.html). Datasets are sorted by project.

## Instructions

1. Update the [source .csv files](https://github.com/rucool/dataset_archiving/tree/master/zooplankton_net_tows/files) with most recent data. Data should be sorted by project.

2. Update the [config files](https://github.com/rucool/dataset_archiving/tree/master/zooplankton_net_tows/config) if necessary.

3. Run [zooplankton_tows_to_erddap](https://github.com/rucool/dataset_archiving/blob/master/zooplankton_net_tows/zooplankton_tows_to_erddap.py) to format the dataset to a NetCDF file for sharing via ERDDAP.

4. Share [output](https://github.com/rucool/dataset_archiving/tree/master/zooplankton_net_tows/output) NetCDF file via [ERDDAP](https://rucool-sampling.marine.rutgers.edu/erddap/index.html).
