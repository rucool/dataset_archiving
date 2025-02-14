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
