### Files ./RC_monitors_in_experiments.json ./RA_monitors_in_experiments.json 
Contain the list of Route Collectors (RIPE RIS and RouteViews), RC, and RIPE Atlas, RA, monitors that provided data in the experiments

### File ./BGPmon_possible_hijacks_exported.csv 
Contains the list of the hijacker-victim pairs detected by the BGPmon service, collected in the [BGPstream events analysis](https://gitlab.com/konstantinosarakadakis/BGPstream) project. The first two columns of the csv file correspond to {hijackerASN, legitimateASN} and the third column corresponds to the type of the hijack (0 for exact prefix hijack, and 1 for subprefix hijack). 


### Folder ./serial_hijackers/
This is the dataset of serial hijackers from the paper "Profiling BGP Serial Hijackers: Capturing Persistent Misbehavior in the Global Routing Table, IMC ’19" downladed from https://github.com/ctestart/BGP-SerialHijackers

- groundtruth_dataset.csv

The original downloaded file with all features of ground truth ASes including their class (0: legitimate ASes, 1: serial hijacker ASes) and AS number ('ASN' column).

- groundtruth_dataset_cropped.csv

A file with only the two columns ASN_number (column #16) and class (column #55) of the original file. 

The file was produced with the command: 

`cat groundtruth_dataset.csv | cut -d"," -f16,55 > groundtruth_dataset_cropped.csv`