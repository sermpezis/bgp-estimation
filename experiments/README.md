This folder contains results from the experiments in the paper [1].

Each folder corresponds to an experiments; folders are named as <experiment id>\_<peering_mux1>\_<peering_mux2> where "peering mux" is the PEERING sites that were used for the legitimate and hijacking announcements. 

Each folder contains the following list of files

- cp_bgpstream_est_mon_as_to_mux_catchment.json
	- a json file mapping the ASN (keys) to the PEERING site (values) where it routes its traffic based on measurements from Route Collectors (from the corresponding BGP paths from the BGPStream service)
- dp_pings_est_as_to_mux_catchment.json
	- a json file mapping the ASN (keys) to the PEERING site (values) where it routes its traffic based on ping measurements

- dp_trace_est_ra_as_to_mux_catchment.json
	- a json file mapping the ASN (keys) to the PEERING site (values) where it routes its traffic based on traceroute measurements from RIPE Atlas monitors 
- <peering_mux1>\_bgpstream_paths.csv
	- a csv with the BGP paths seen by the monitors when only the <peering_mux1> announces the prefix; format {route collector ID, monitor ASN, BGP path}
- <peering_mux2>\_bgpstream_paths.csv
	- a csv with the BGP paths seen by the monitors when only the <peering_mux2> announces the prefix; format {route collector ID, monitor ASN, BGP path}
- <peering_mux1>\_<peering_mux2>\_bgpstream_paths.csv
	- a csv with the BGP paths seen by the monitors when both <peering_mux1> and <peering_mux2> announce the prefix (one assumed to be the victim and the other the hijacker); format {route collector ID, monitor ASN, BGP path}
- dp_pings_per_asn.json
	- a json file mapping the ASN (keys) to the number of pings needed to reply with a ping (values) used for estimating the ping failure probability
