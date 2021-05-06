#!/usr/bin/env python3

import argparse
import glob
import os
import utils

parser = argparse.ArgumentParser(description="translate DP probes from ASNs to mux catchment")
parser.add_argument('-c', '--cp', dest='cp_dir', type=str,
                    help='directory with control-plane information', required=True)
parser.add_argument('-d', '--dp', dest='dp_dir', type=str,
                    help='directory with data-plane information', required=True)
args = parser.parse_args()

cp_dir = args.cp_dir.rstrip('/')
assert os.path.isdir(cp_dir)
dp_dir = args.dp_dir.rstrip('/')
assert os.path.isdir(dp_dir)
ping_dir = "{}/pings".format(dp_dir)
assert os.path.isdir(ping_dir)
raw_ping_dir = "{}/raw".format(ping_dir)
assert os.path.isdir(raw_ping_dir)

assert os.path.isfile("{}/pingable_ip_to_asn.json".format(ping_dir))
pingable_ip_to_asn = utils.load_json("{}/pingable_ip_to_asn.json".format(ping_dir))

assert os.path.isfile("{}/asn_to_pingable_ips.json".format(ping_dir))
asn_to_pingable_ips = utils.load_json("{}/asn_to_pingable_ips.json".format(ping_dir))

assert os.path.isfile("{}/mux_to_origin.json".format(cp_dir))
mux_to_origin = utils.load_json("{}/mux_to_origin.json".format(cp_dir))

est_mux_catchment = {}
pings_per_asn = {}
for ping_result_file in glob.glob("{}/*.json".format(raw_ping_dir)):
    ip = ping_result_file.split('/')[-1].split(".json")[0]
    try:
        ping_result = utils.load_json(ping_result_file)["received"]
    except:
        continue
    asn = pingable_ip_to_asn[ip]
    assert str(asn) in asn_to_pingable_ips
    assert asn not in pings_per_asn
    ip_index = asn_to_pingable_ips[str(asn)].index(ip)
    pings_per_asn[asn] = ip_index + 1
    mux = None
    if len(ping_result) == 1:
        mux = ping_result[0]
    if mux and mux in mux_to_origin:
        if asn not in est_mux_catchment:
            est_mux_catchment[asn] = set()
        est_mux_catchment[asn].add(mux)
for asn in est_mux_catchment:
    est_mux_catchment[asn] = list(est_mux_catchment[asn])

# store the information on estimated AS and mux catchments
utils.dump_json('{}/est_as_to_mux_catchment.json'.format(ping_dir), est_mux_catchment)
utils.dump_json('{}/pings_per_asn.json'.format(ping_dir), pings_per_asn)
