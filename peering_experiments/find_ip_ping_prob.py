#!/usr/bin/env python3

import argparse
import os
import glob
import json
import sys
import numpy as np
sys.path.insert(0, "../pfx2as")
from pprint import pprint as pp

parser = argparse.ArgumentParser(description="find probability of IPs being pingable per ASN")
parser.add_argument("-a", "--asn_to_pingable_ips", dest="asn_to_pingable_ips", type=str, help="file with ASN to pingable IPs mapping", required=True)
parser.add_argument("-p", "--pingable_ip_to_asn", dest="pingable_ip_to_asn", type=str, help="file with pingable IP to ASN mapping", required=True)
parser.add_argument("-r", "--raw_pings_answered", dest="raw_pings_answered", type=str, help="directory with raw pings", required=True)
parser.add_argument("-o", "--out_prob_file", dest="out_prob_file", type=str, help="out json file with ping probabilities", default="out_prob.json")
args = parser.parse_args()

assert os.path.isfile(args.asn_to_pingable_ips)
assert os.path.isfile(args.pingable_ip_to_asn)
raw_pings_dir = args.raw_pings_answered.rstrip('/')
assert os.path.isdir(raw_pings_dir)

with open(args.asn_to_pingable_ips, 'r') as f:
    asn_to_pingable_ips = json.load(f)

with open(args.pingable_ip_to_asn, 'r') as f:
    pingable_ip_to_asn = json.load(f)

answered_ips = set()
for ping_file in glob.glob("{}/*.json".format(raw_pings_dir)):
    with open(ping_file, 'r') as f:
        try:
            ping_res = json.load(f)
        except:
            continue
    if not ping_res["received"]:
        continue
    ip = ping_file.split('/')[-1].split(".json")[0]
    answered_ips.add(ip)

ip_ping_probs = []
seen_asns = set()
for ip in answered_ips:
    assert ip in pingable_ip_to_asn
    asn = pingable_ip_to_asn[ip]
    assert str(asn) in asn_to_pingable_ips
    assert asn not in seen_asns
    seen_asns.add(asn)
    ip_index = asn_to_pingable_ips[str(asn)].index(ip)
    ip_ping_probs.append(1.0/(ip_index + 1))

print("MEDIAN = {}".format(np.median(ip_ping_probs)))
print("MEAN = {}".format(np.mean(ip_ping_probs)))

with open(args.out_prob_file, 'w') as f:
    json.dump(ip_ping_probs, f)
