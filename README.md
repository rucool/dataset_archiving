# dataset_archiving
A collection of tools to post-process and prepare datasets for archiving at the National Centers for Environmental Information (NCEI), Northeast Fisheries Science Center (NEFSC) and Mid-Atlantic Acoustic Telemetry Observation System (MATOS)

## Installation Instructions
Add the channel conda-forge to your .condarc. You can find out more about conda-forge from their website: https://conda-forge.org/

`conda config --add channels conda-forge`

Clone the dataset_archiving repository

`git clone https://github.com/rucool/dataset_archiving.git`

Change your current working directory to the location that you downloaded dataset_archiving. 

`cd /Users/garzio/Documents/repo/dataset_archiving/`

Create conda environment from the included environment.yml file:

`conda env create -f environment.yml`

Once the environment is done building, activate the environment:

`conda activate dataset_archiving`

Install the toolbox to the conda environment from the root directory of the dataset_archiving toolbox:

`pip install .`

The toolbox should now be installed to your conda environment.

## Post-processing Instructions

Download glider .nc files to your local machine using (download_glider_dataset.py)[https://github.com/rucool/dataset_archiving/blob/master/download_glider_dataset.py]

Post-process and make quick plots of the glider data variables for a quick check before archiving the datasets in the appropriate archive:
1. (pH glider processing)[https://github.com/rucool/dataset_archiving/tree/master/pH_glider]
2. (acoustic glider processing (e.g. AZFP and DMON))[https://github.com/rucool/dataset_archiving/tree/master/acoustics_glider]
