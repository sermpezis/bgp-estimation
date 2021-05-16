This folder contain scripts, datasets, examples, etc., to run BGP Interent scale simulations for hijack events.

### Folder ./CAIDA AS-graph/
This is the folder to place the AS-relationship dataset. In the paper [1] we have used the dataset from 2019-08-01 (`/CAIDA AS-graph/20190801.as-rel2.txt`), which we include here for convenience. You can find newer / different datasets at the [CAIDA's AS relationship site]( https://www.caida.org/catalog/datasets/as-relationships/)

### Folder ./BGP_simulator
This folder containts the python scripts for the simulator. The files are copied here (for convenience) from the main [BGP simulator github project](https://github.com/FORTH-ICS-INSPIRE/anycast_catchment_prediction); please refer there if you need more information on the simulator

### Folder ./examples
Contains examples and scripts that are needed to conduct simulation experiments as in the paper [1].

- util_functions.py     contains utility functions needed for the simulations
- example_sims_impact_estimation_vs_random_mon_and_RC_and_RA.py     
    - example script that runs a number of simulations with hijacks (random hijacker-victim pairs), calculates the impact of hijacks and the observations of monitors, and writes the outputs in a file
- example_sims_impact_estimation_vs_random_mon_and_RC_and_RA__BGPmon_events.py     
    - a variant of the above example script where the hijacker-victim pairs are selected from the real events seen by the BGPmon service 
- example_sims_impact_estimation_vs_random_mon_and_RC_and_RA__Serial_hijackers.py  
    - a variant of the above example script where the hijacker is selected from the list of serial hijackers identified in the (Testart et al, 2018, IMC paper)

**How to run the code**

An example that would run *10* simulation runs for Type-*0* hijacks for the CAIDA AS relationships dataset *20190801* is the following

`python3  example_sims_impact_estimation_vs_random_mon_and_RC_and_RA.py 10  0 20190801`


### Folder ./data
Contains data that are needed in the examples scripts (and have been used in the paper [1]), namely

- the list of Route Collectors (RIPE RIS and RouteViews) / RIPE Atlas monitors that provided data in the experiments
- the list of the hijacker-victim pairs detected by the BGPmon service, collected in the [BGPstream events analysis](https://gitlab.com/konstantinosarakadakis/BGPstream) project
- the list of serial hijackers from the paper "Profiling BGP Serial Hijackers: Capturing Persistent Misbehavior in the Global Routing Table, IMC ’19" downladed from https://github.com/ctestart/BGP-SerialHijackers


