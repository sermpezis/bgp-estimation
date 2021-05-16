## PRE-REQUISITES

### NEEDED PACKAGES

* python2
* python3
* pytricia
* netaddr
* scapy
* jsonschema
* libbgpstream
* pybgpsttream
* socat

### NEEDED CREDENTIALS

You need to apply to PEERING for a new account and get credentials, and also get an ATLAS api key
for data plane experiments (e.g., traceroutes).

* ./peering_client/certs/client.crt
* ./peering_client/certs/client.key
* ./atlas_key.txt

## END-TO-END PEERING EXP SCRIPT

```
usage: run_end_to_end_experiment.py [-h] --m1 MUX_1 --m2 MUX_2
```

This runs the `run_peering_exp.py` to announce a prefix from two PEERING muxes and then withdraw it.
In the meanwhile, it collects the results from the control and data plane (see produced files
in the following sections). Note that the files `asn_to_pingable_ips.json` and `pingable_ip_to_asn.json`
are templated and you should put your own data there (see templates as well as the `AUX SCRIPTS` section of
current README).

## MAIN PEERING EXP SCRIPT

### Run PEERING MOAS experiment

```
usage: run_peering_exp.py [-h]

    -e EXPERIMENT_JSON      (required, give the location of the announcement json of the experiment)
    
    [-p PEERING_PEERS_JSON] (default='./peers.json')
    
    [-i IP_TO_AS]           (default="../pfx2as/data/dbs/2019_10_db.json")
    
    [-t]                    (run traceroutes, default: not activated)
    
    [-d]                    (run dp probing, default: not activated)
    
    [-b]                    (run BGPStream path collection, default: not activated)
    
    [-a]                    (run analysis, default: not activated)
    
    [-x EXISTING_EXP_DIR]   (default="")
```

Creates the following folders and files:

```
experiments/<EXP_TITLE>_Y..._M..D..H..M...
   
    <EXP_TITLE>_Y..._M..D..H..M....json
   
    control_plane
       
        <EXPERIMENT_JSON>
       
        asn_to_u_mux.json
       
        asn_to_u_mux_rel.json
       
        available_muxes.json
       
        bgpstream_paths_for_prefix_<PREFIX>_<START>_<END>.csv
       
        bird_mux_status.json
       
        exp_configured_muxes.json
       
        live_muxes.json
       
        metadata.json
       
        mux_to_u_asn.json
       
        mux_to_u_asn_rel.json
       
        mux_to_origin.json
       
        origin_to_mux.json
       
        peer.json
       
        vpn_mux_status.json
       
        est_as_to_mux_catchment.json
       
        est_mon_to_mux_catchment.json
   
    data_plane
       
        pings
           
            raw
               
                <IP...>.json
           
            asn_to_pingable_ips.json
           
            pingable_ip_to_asn.json
           
            pings_per_asn.json
           
            tap_macs.json
           
            est_as_to_mux_catchment.json

        traceroutes
           
            msm_info.json
           
            prb_info.json
           
            est_as_to_last_as_catchment.json
           
            est_as_to_mux_catchment.json
           
            as_level_paths.csv
           
            est_ra_to_last_as_catchment.json
           
            est_ra_to_mux_catchment.json
```

## SCRIPTS CALLED BY MAIN EXP SCRIPT

### Issue pings to pingable IPs per ASN

```
usage: issue_pings_to_asns.py [-h]

    [--ping_ip_to_asn PINGABLE_IP_TO_ASN]   (default="./pingable_ip_to_asn.json")

    [--asn_to_ping_ips ASN_TO_PINGABLE_IPS] (default="./asn_to_pingable_ips.json"

    [--ip_to_as IP_TO_AS]                   (default="../pfx2as/data/dbs/2019_10_db.json")

    [--asn_alloc ASN_ALLOC]                 (default="../pfx2as/data/as_allocation/wikipedia_asn_allocation.json")

    --cp_dir CP_DIR                         (required, give the location of the control_plane sub-directory of experiment)

    --dp_dir DP_DIR                         (required, give the location of the data plane sub-directory of experiment)

    [--parallel_ping_num PARALLEL_PING_NUM] (default=50)

    [--source_ip SOURCE_IP]                 (default="184.164.243.1")

    [--max_ases_ok_ping MAX_ASES_OK_PING]   (default=10000)
```

Writes the following files:

```
<DP_DIR>/pings/raw/<IP...>.json

<DP_DIR>/pings/pingable_ip_to_asn.json

<DP_DIR>/pings/asn_to_pingable_ips.json

<DP_DIR>/pings/tap_macs.json
```

### Translate DP probes from ASNs to mux catchment

```
usage: translate_dp_probes_to_catchment.py [-h]

-c CP_DIR    (required, give the location of the control_plane sub-directory of experiment)

-d DP_DIR    (required, give the location of the data plane sub-directory of experiment)
```

Writes the following files:

```
<DP_DIR>/pings/est_as_to_mux_catchment.json

<DP_DIR>/pings/pings_per_asn.json
```

### Execute traceroutes from RA probes to prefix

```
usage: issue_traceroutes_to_prefix.py [-h]

    -t TARGET_PREFIX        (required, give the target prefix)

    [-m MAX_PROBES_PER_AS]  (default=1)

    [-k ATLAS_KEY_FILE]     (default='./atlas_key.txt')

    [-o TIME_OFFSET]        (default=60)

    -d MSM_DIR              (required, give the location of the msm dir)
```

Writes the following files:
```
<MSM_DIR>/traceroutes/msm_info.json

<MSM_DIR>/traeroutes/prb_info.json
```

### Fetch and parse traceroutes from RA probes to prefix (to-catchment translation)

```
usage: translate_traceroutes_to_catchment.py [-h]
  
    [--ip_to_as IP_TO_AS]   (default="../pfx2as/data/dbs/2019_10_db.json")
  
    -d DP_DIR               (required, give the location of the data plane sub-directory of experiment)
  
    -c CP_DIR               (required, give the location of the control plane sub-directory of experiment)
```

Writes the following files:

```
<DP_DIR>/traceroutes/est_as_to_last_as_catchment.json

<DP_DIR>/traceroutes/est_as_to_mux_catchment.json

<DP_DIR>/traceroutes/as_level_paths.csv

<DP_DIR>/traceroutes/est_ra_to_last_as_catchment.json

<DP_DIR>/traceroutes/est_ra_to_mux_catchment.json
```

### Fetch bgpstream paths (by RIB reconstruction via BGP updates) for a certain prefix

```
upd_get_bgpstream_paths_for_prefix.py [-h]

    -p PREFIX       (required, give the prefix to look for)

    -s START_TIME   (required, start time of lookup)

    -e END_TIME     (required, end time of lookup)

    -c CP_DIR
```

Writes the following files:

```
<CP_DIR>/bgpstream_paths_for_prefix_<PREFIX>_<START>_<END>.csv
```

### Translate BGPStream paths to catchment

```
usage: translate_bgpstream_paths_to_catchment.py [-h]

    -b BGPSTREAM_PATHS_FILE (required, give the location of the path csv)

    -c CP_DIR               (required, give the location of the control-plane sub-directory of experiment)
```

Writes the following files:

```
<CP_DIR>/est_as_to_mux_catchment.json

<CP_DIR>/est_mon_to_mux_catchment.json
```

### Produce final experiment information

```
usage: parse_final_exp_info.py [-h] -e EXP_DIR  (required, give the location of the experiment)
```

Writes the following files:

```
<EXP_DIR>/<EXP_TITLE>_Y..._M..D..H..M....json
```

## AUX SCRIPTS

## Calculate pingable IPs per ASN (and IP-to-ASN mappings)

In our experiments, we used datasets from [ANT-Labs (Internet Address History)](https://ant.isi.edu/datasets/all.html) which we cannot publish or re-distribute.
Please request them directly ANT-Labs; they should be available for most researchers. 

The pingable IPs to ASN file is the `asn_to_pingable_ips.json` - in this folder you can find an empty placeholder of this file (e.g., to be filled with ANT-Labs dataset or any other dataset). If you want to use your own dataset or any dataset (other than ANT-Labs), please contact @vkotronis for more information! 

```
usage: calculate_pingable_ips_per_asn.py [-h]

    [--pingable_ips PINGABLE_IPS]   (default="../internet_address_history_it86w-20190624.fsdb.bz2")

    [--ip_to_as IP_TO_AS]           (default="../pfx2as/data/dbs/2019_10_db.json")

    [--asn_alloc ASN_ALLOC]         (default="../pfx2as/data/as_allocation/wikipedia_asn_allocation.json")

    [--out_dir OUT_DIR]             (default='.')

    [--ips_per_asn IPS_PER_ASN]     (default=10)

    [--ip_score IP_SCORE]           (default=90)

    [--asn_coverage ASN_COVERAGE]   (default=100)
```

Writes the following files:

```
<OUT_DIR>/pingable_ip_to_asn.json

<OUT_DIR>/asn_to_pingable_ips.json
```
