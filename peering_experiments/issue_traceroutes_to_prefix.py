#!/usr/bin/env python3

import argparse
import sys
import utils
from netaddr import IPNetwork
# remove after testing!
from pprint import pprint as pp


MAX_PRBS_PER_MSM = 1000
CREDITS_PER_TRACE = 60


parser = argparse.ArgumentParser(description="execute traceroutes from RA probes to prefix")
parser.add_argument('-t', '--target_prefix', dest='target_prefix', type=str,
                     help='target IP prefix (CIDR format)', required=True)
parser.add_argument('-m', '--max_probes', dest='max_probes_per_as', type=int,
                     help='maximum number of probes to consider per AS', default=1)
parser.add_argument('-k', '--atlas_key_file', dest='atlas_key_file', type=str,
                    help='atlas key file', default='./atlas_key.txt')
parser.add_argument('-o', '--time_offset', dest='time_offset', type=int,
                    help='time offset to launch msms (seconds)', default=60)
parser.add_argument('-d', '--dir', dest='msm_dir', type=str,
                    help='directory where measurement info will be stored', required=True)
args = parser.parse_args()

# create the needed directory
msm_dir = "{}/traceroutes".format(args.msm_dir.rstrip('/'))
utils.create_dir(msm_dir)

# validate the target prefix
if not utils.is_valid_prefix(args.target_prefix):
    print('Target prefix {} is invalid! Aborting...'.format(args.target_prefix))
    sys.exit(1)
target_prefix = IPNetwork(args.target_prefix)
available_target_ips = [str(ip) for ip in target_prefix]
# remove network and broadcast IPs
del available_target_ips[0]
del available_target_ips[-1]

# collect probes that will be used for the measurements
all_probe_info = utils.fetch_probe_info()
asns_to_probe_ids = utils.map_asns_to_probe_ids(all_probe_info)
utils.keep_max_prb_per_asn(asns_to_probe_ids, args.max_probes_per_as)
all_msm_probe_ids = set()
for asn in asns_to_probe_ids:
    all_msm_probe_ids.update(asns_to_probe_ids[asn])
all_msm_probe_info = {}
for prb_id in all_msm_probe_ids:
    all_msm_probe_info[prb_id] = all_probe_info[prb_id]
# store msm prb info
utils.dump_json('{}/prb_info.json'.format(msm_dir), all_msm_probe_info)

# group the probes in buckets
prb_buckets = []
all_msm_probe_ids_list = list(all_msm_probe_ids)
for i in range(0, len(all_msm_probe_ids_list), MAX_PRBS_PER_MSM):
    prb_bucket = all_msm_probe_ids_list[i:i+MAX_PRBS_PER_MSM]
    prb_buckets.append(prb_bucket)

# retrieve atlas key for running the measurements
assert args.atlas_key_file is not None, 'You need to supply an ATLAS key file!'
atlas_key = ""
with open(args.atlas_key_file, 'r') as f:
    atlas_key = f.readline().rstrip()

# calculate projected credits
credits = sum([len(prb_bucket)*CREDITS_PER_TRACE for prb_bucket in prb_buckets])

# issue traceroutes from all probes per bucket towards a certain IP address (try to load-balance within the prefix)
msm_info = {
    'credits': credits,
    'ids': []
}
for i, prb_bucket in enumerate(prb_buckets):
    target_ip = available_target_ips[i % len(available_target_ips)]
    msm_id = utils.issue_traceroute_msms(prb_bucket, target_ip, args.time_offset, atlas_key)
    if msm_id is not None:
        msm_info['ids'].append(msm_id)

# store issued msm info
utils.dump_json('{}/msm_info.json'.format(msm_dir), msm_info)
