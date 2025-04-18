# pH glider
A collection of tools to post-process and prepare datasets related to pH glider deployments for archiving at the National Centers for Environmental Information (NCEI) and in Rutgers ERDDAP server.

pH glider datasets are QC'd and archived in NCEI's [Ocean Carbon and Acidification Data System (OCADS)](https://www.ncei.noaa.gov/products/ocean-carbon-acidification-data-system).

## Post-processing Instructions

1. For each deployment, download glider .nc files to your local machine using [download_glider_dataset.py](https://github.com/rucool/dataset_archiving/blob/master/download_glider_dataset.py) (add_engineering_vars can be False)

2. Post-process ([phglider_to_ncei.py](https://github.com/rucool/dataset_archiving/blob/master/pH_glider/phglider_to_ncei.py)) and make quick plots ([plot_phglider_ncei.py](https://github.com/rucool/dataset_archiving/blob/master/pH_glider/plot_phglider_ncei.py)) of the glider data variables for a quick check before archiving.

3. Submit the dataset in the OCADS submission data portal
