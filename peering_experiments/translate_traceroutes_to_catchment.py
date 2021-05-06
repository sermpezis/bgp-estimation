#!/usr/bin/env python3

import argparse
import os
import sys
sys.path.insert(0, "../pfx2as")
import ip_to_as_lib as lib
import utils
import csv

parser = argparse.ArgumentParser(description="fetch and parse traceroutes from RA probes to prefix")
parser.add_argument('-i', "--ip_to_as", dest='ip_to_as', type=str, help='ip (pfx) to AS db json', default="../pfx2as/data/dbs/2019_10_db.json")
parser.add_argument('-d', '--dp', dest='dp_dir', type=str,
                    help='directory with data-plane information', required=True)
parser.add_argument('-c', '--cp', dest='cp_dir', type=str,
                    help='directory with control-plane information', required=True)
args = parser.parse_args()

# load needed information on probes and msm ids
dp_dir = "{}/traceroutes".format(args.dp_dir.rstrip('/'))
msm_info_file = '{}/msm_info.json'.format(dp_dir)
assert os.path.isfile(msm_info_file)
prb_info_file = '{}/prb_info.json'.format(dp_dir)
assert os.path.isfile(prb_info_file)
msm_info = utils.load_json(msm_info_file)
prb_info = utils.load_json(prb_info_file)
cp_dir = args.cp_dir.rstrip("/")
assert os.path.isfile('{}/asn_to_u_mux.json'.format(cp_dir))
asn_to_u_mux = utils.load_json('{}/asn_to_u_mux.json'.format(cp_dir))

# load IPtoASN mapping
ip_to_as_db = lib.dict_list_to_set(lib.import_json(args.ip_to_as))
ip_to_as_pyt = lib.convert_json_to_pyt(ip_to_as_db)

# estimate catchment on the AS-level using the last valid hop(s) in the traceroute
est_as_catchment = {}
est_src_catchment = {}
with open("{}/as_level_paths.csv".format(dp_dir), 'w') as csvfile:
    writer = csv.writer(csvfile, delimiter='\t')
    #writer.writerow(["prb", "prb_asn", "as_path"])
    for msm_id in msm_info['ids']:
        msm_result = utils.fetch_msm_result(msm_id)
        for trace in msm_result:
            if 'prb_id' not in trace:
                continue
            src_prb_id = trace['prb_id']
            src_prb_asn = prb_info[str(src_prb_id)]['asn_v4']
            if 'result' not in trace:
                continue
            as_level_path = []
            for hop in sorted(trace['result'], key=lambda x: x['hop']):
                if 'result' not in hop:
                    continue
                hop_results = hop['result']
                these_hop_ips = set()
                for hop_result in hop_results:
                    if 'from' in hop_result:
                        ip = hop_result['from']
                        if utils.is_valid_ip(ip):
                            these_hop_ips.add(ip)

                hop_asns = set()
                for ip in these_hop_ips:
                    if ip in ip_to_as_pyt:
                        asns = ip_to_as_pyt[ip]
                        if asns and len(asns) == 1:
                            hop_asns.add(list(asns)[0])
                if len(hop_asns) == 1:
                    as_level_path.append(list(hop_asns)[0])
            as_level_path.insert(0, src_prb_asn)
            for asn in as_level_path:
                if asn not in est_as_catchment:
                    est_as_catchment[asn] = set()
                est_as_catchment[asn].add(as_level_path[-1])
            writer.writerow([src_prb_id, src_prb_asn, ','.join(map(str, as_level_path))])
            if src_prb_asn not in est_src_catchment:
                est_src_catchment[src_prb_asn] = set()
            est_src_catchment[src_prb_asn].add(as_level_path[-1])

# now translate estimated AS catchment to mux catchment
est_mux_catchment = {}
for asn in est_as_catchment:
    muxes = set()
    for catch_asn in est_as_catchment[asn]:
        if str(catch_asn) in asn_to_u_mux:
            muxes.add(asn_to_u_mux[str(catch_asn)])
    if len(muxes) > 0:
        est_mux_catchment[asn] = list(muxes)
    est_as_catchment[asn] = list(est_as_catchment[asn])

# and RA (src) AS catchment to mux catchment
est_src_mux_catchment = {}
for asn in est_src_catchment:
    muxes = set()
    for catch_asn in est_src_catchment[asn]:
        if str(catch_asn) in asn_to_u_mux:
            muxes.add(asn_to_u_mux[str(catch_asn)])
    if len(muxes) > 0:
        est_src_mux_catchment[asn] = list(muxes)
    est_src_catchment[asn] = list(est_src_catchment[asn])

# store the information on estimated AS and mux catchments
utils.dump_json('{}/est_as_to_last_as_catchment.json'.format(dp_dir), est_as_catchment)
utils.dump_json('{}/est_as_to_mux_catchment.json'.format(dp_dir), est_mux_catchment)
utils.dump_json('{}/est_ra_to_last_as_catchment.json'.format(dp_dir), est_src_catchment)
utils.dump_json('{}/est_ra_to_mux_catchment.json'.format(dp_dir), est_src_mux_catchment)
