# Acoustics glider

Author: Lori Garzio _lgarzio@marine.rutgers.edu_

A collection of tools to post-process and prepare datasets related to glider deployments with acoustics sensors on board (e.g. AZFP, DMON) for archiving at the National Centers for Environmental Information (NCEI) and in Rutgers ERDDAP server.

AZFP (Acoustic Zooplankton Fish Profiler) glider datasets are QC'd and archived in NCEI's [Water Column Sonar Data](https://www.ncei.noaa.gov/products/water-column-sonar-data) along with the raw AZFP data files and post-processed AZFP data.

DMON (WHOI Digital Acoustic Monitoring Instrument) glider datasets are QC'd and archived in NCEI's [Passive Acoustic Data Archive](https://www.ncei.noaa.gov/products/passive-acoustic-data) along with the .wav audio files from the DMON

## Post-processing Instructions

1. For each deployment, download glider .nc files to your local machine using [download_glider_dataset.py](https://github.com/rucool/dataset_archiving/blob/master/download_glider_dataset.py) For DMON datasets, add_engineering_vars = False and for AZFP datasets, add_engineering_vars = True.

2. Post-process ([acoustics_glider_to_archive.py](https://github.com/rucool/dataset_archiving/blob/master/acoustics_glider/acoustics_glider_to_archive.py)) and make quick plots ([plot_acoustics_glider.py](https://github.com/rucool/dataset_archiving/blob/master/acoustics_glider/plot_acoustics_glider.py)) of the glider data variables for a quick check before archiving

### DMON raw data files - this must be done on a PC computer

1. Download raw .dtg files from the server

2. Process the raw files to .wav using d3read software.

3. [sort_dmon_wav_files.py](https://github.com/rucool/dataset_archiving/blob/master/acoustics_glider/sort_dmon_wav_files.py): Renames all files to use the deployment ID, figures out which files contain deployment data, sorts those files into the "files_to_archive" folder, and determines if any files need to be split to remove to remove non-deployment data. Spits out a summary .csv file so you can figure out if you need to split the .wav files.

4. If files need to be split, use Mark Baumgartner's reformat_dmon_wav_files.sav program to split the .wav files in the "renamed" directory into smaller files. Must split ALL of the files because sometimes the program has issues splitting specific files. 

    a. Navigate to:
	
        Program Files > NV5 > IDL91 > IDL Virtual Machine
		
    b. In the VM, open the program: 
	
        Documents > DMON > software > reformat_dmon_wav_files.sav
		
    c. Choose the folder with DMON data: 
	
        Documents > DMON > yyyy > deployment > from-dmon > renamed
		
    d. Choose the folder to save split files: 
	
        Documents > DMON > yyyy > deployment > from-dmon > split_files
		
    e. Click Go!

5. [sort_split_dmon_wav_files.py](https://github.com/rucool/dataset_archiving/blob/master/acoustics_glider/sort_split_dmon_wav_files.py): Move the appropriate split .wav files that contain deployment data into the "files_to_archive" folder.