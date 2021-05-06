#!/usr/bin/env python3

import argparse
import csv
import utils
import os

# PEERING ASes, at least one should appear as origin in all announcements
PEERING_ASNS = [
    47065,
    33207,
    61574,
    61575,
    61576,
    263842,
    263843,
    263844
]


parser = argparse.ArgumentParser(description="translate BGPStream paths to catchment")
parser.add_argument('-b', '--bgpstream_paths', dest='bgpstream_paths_file', type=str,
                    help='file with bgpstream-seen paths towards anycasters', required=True)
parser.add_argument('-c', '--cp', dest='cp_dir', type=str,
                    help='directory with control-plane information', required=True)
args = parser.parse_args()

# load aux information for disambiguating anycast catchment
cp_dir = args.cp_dir.rstrip('/')
assert os.path.isfile("{}/origin_to_mux.json".format(cp_dir))
origin_to_mux = utils.load_json("{}/origin_to_mux.json".format(cp_dir))

# estimate catchment on the AS-level using the expected origin hop in the path
est_as_to_mux_catchment = {}
est_mon_to_mux_catchment = {}
with open(args.bgpstream_paths_file, 'r') as f:
    reader = csv.reader(f, delimiter='\t')
    for row in reader:
        asns = list(map(int, row[2].split(',')))
        # ignore empty or unreasonable paths
        if len(asns) <= 3:
            continue
        # ignore paths that are not towards our ASN (origin)
        if str(asns[-2]) not in origin_to_mux:
            continue
        # ignore paths that do not pass via PEERING
        if asns[-3] not in PEERING_ASNS:
            continue
        # ignore paths for which the peer ASN is not the last AS on-path
        caught_mon = int(row[1])
        if caught_mon != asns[0]:
            continue
        # find the last occurence of a PEERING ASN before the update is propagated to its peer
        peering_origin_index = asns.index(asns[-3])
        caught_asns = asns[:peering_origin_index]
        mux = origin_to_mux[str(asns[-2])][0]
        for asn in caught_asns:
            if asn not in est_as_to_mux_catchment:
                est_as_to_mux_catchment[asn] = set()
            est_as_to_mux_catchment[asn].add(mux)
        if caught_mon not in est_mon_to_mux_catchment:
            est_mon_to_mux_catchment[caught_mon] = set()
        est_mon_to_mux_catchment[caught_mon].add(mux)

# store the information on estimated catchment
for asn in est_as_to_mux_catchment:
    est_as_to_mux_catchment[asn] = list(est_as_to_mux_catchment[asn])
for mon in est_mon_to_mux_catchment:
    est_mon_to_mux_catchment[mon] = list(est_mon_to_mux_catchment[mon])
utils.dump_json('{}/est_as_to_mux_catchment.json'.format(cp_dir), est_as_to_mux_catchment)
utils.dump_json('{}/est_mon_to_mux_catchment.json'.format(cp_dir), est_mon_to_mux_catchment)
