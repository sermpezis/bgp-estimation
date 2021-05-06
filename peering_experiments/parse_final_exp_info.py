#!/usr/bin/env python3

import argparse
import json
import os

parser = argparse.ArgumentParser(description="produce final experiment information")
parser.add_argument('-e', '--exp', dest='exp_dir', type=str,
                    help='directory with experiment information', required=True)
args = parser.parse_args()

exp_dir = args.exp_dir.rstrip('/')
assert os.path.isdir(exp_dir)
cp_dir = "{}/control_plane".format(exp_dir)
assert os.path.isdir(cp_dir)
dp_dir = "{}/data_plane".format(exp_dir)
assert os.path.isdir(dp_dir)

exp_data = {
    "title": None, # string
    "prefix": None, #string
    "muxes": [], # list
    "mux_to_unique_peering_peer": {}, # dict
    "mux_to_origin": {}, #dict
    "time_info": {
        "exact_timestamp": None, #float
        "bgpstream_check_started": None, # float
        "bgpstream_check_ended": None, # fLoat
    },
    "catchment": {
        "cp": {}, # dict (mux to asn)
        "dp": {
            "traceroutes": {}, # dict (mux to asn)
            "pings": {} # dict (mux to asn)
        }
    },
    "total_num_of_asns_in_catchment": {
        "cp": 0,
        "dp": {
            "traceroutes": 0,
            "pings": 0
        }
    }
}

exp_data["title"] = exp_dir.split("/")[-1]
with open("{}/{}.json".format(cp_dir, exp_data["title"].split("_Y")[0]), "r") as f:
    exp_data["prefix"] = list(json.load(f).keys())[0]
with open("{}/exp_configured_muxes.json".format(cp_dir), "r") as f:
    exp_data["muxes"] = json.load(f)
with open("{}/metadata.json".format(cp_dir), "r") as f:
    metadata = json.load(f)
    exp_data["time_info"]["exact_timestamp"] = metadata["timestamp"]
    exp_data["time_info"]["bgpstream_check_started"] = metadata["start_check"]
    exp_data["time_info"]["bgpstream_check_ended"] = metadata["end_check"]
with open("{}/asn_to_u_mux.json".format(cp_dir), "r") as f:
    asn_to_u_mux = json.load(f)
    for asn in asn_to_u_mux:
        mux = asn_to_u_mux[asn]
        if mux not in exp_data["mux_to_unique_peering_peer"]:
            exp_data["mux_to_unique_peering_peer"][mux] = set()
        exp_data["mux_to_unique_peering_peer"][mux].add(int(asn))
    for mux in exp_data["mux_to_unique_peering_peer"]:
        exp_data["mux_to_unique_peering_peer"][mux] = list(exp_data["mux_to_unique_peering_peer"][mux])

for mux in exp_data["muxes"]:
    exp_data["catchment"]["cp"][mux] = set()
    exp_data["catchment"]["dp"]["pings"][mux] = set()
    exp_data["catchment"]["dp"]["traceroutes"][mux] = set()

with open("{}/est_as_to_mux_catchment.json".format(cp_dir), "r") as f:
    cp_as_to_mux_catchment = json.load(f)
    for asn in cp_as_to_mux_catchment:
        if len(cp_as_to_mux_catchment[asn]) == 1:
            mux = cp_as_to_mux_catchment[asn][0]
            exp_data["catchment"]["cp"][mux].add(asn)

with open("{}/pings/est_as_to_mux_catchment.json".format(dp_dir), "r") as f:
    ping_as_to_mux_catchment = json.load(f)
    for asn in ping_as_to_mux_catchment:
        if len(ping_as_to_mux_catchment[asn]) == 1:
            mux = ping_as_to_mux_catchment[asn][0]
            exp_data["catchment"]["dp"]["pings"][mux].add(asn)

with open("{}/traceroutes/est_as_to_mux_catchment.json".format(dp_dir), "r") as f:
    trace_as_to_mux_catchment = json.load(f)
    for asn in trace_as_to_mux_catchment:
        if len(trace_as_to_mux_catchment[asn]) == 1:
            mux = trace_as_to_mux_catchment[asn][0]
            exp_data["catchment"]["dp"]["traceroutes"][mux].add(asn)

for mux in exp_data["muxes"]:
    exp_data["catchment"]["cp"][mux] = list(exp_data["catchment"]["cp"][mux])
    exp_data["catchment"]["dp"]["pings"][mux] = list(exp_data["catchment"]["dp"]["pings"][mux])
    exp_data["catchment"]["dp"]["traceroutes"][mux] = list(exp_data["catchment"]["dp"]["traceroutes"][mux])

exp_data["total_num_of_asns_in_catchment"]["cp"] = sum([len(asns) for asns in exp_data["catchment"]["cp"].values()])
exp_data["total_num_of_asns_in_catchment"]["dp"]["pings"] = sum([len(asns) for asns in exp_data["catchment"]["dp"]["pings"].values()])
exp_data["total_num_of_asns_in_catchment"]["dp"]["traceroutes"] = sum([len(asns) for asns in exp_data["catchment"]["dp"]["traceroutes"].values()])

with open("{}/{}.json".format(exp_dir, exp_data["title"]), "w") as f:
    json.dump(exp_data, f)
