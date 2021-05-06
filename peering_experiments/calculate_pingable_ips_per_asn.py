#!/usr/bin/env python3

import argparse
import bz2
import os
import re
import sys
sys.path.insert(0, "../pfx2as")
import ip_to_as_lib as lib
import utils

parser = argparse.ArgumentParser(description="calculate pingable IPs per ASN")
parser.add_argument("--pingable_ips", dest="pingable_ips", type=str, help="file with pingable IPs per /24", default="/home/vkotronis/Downloads/internet_address_history_it86w-20190624.fsdb.bz2")
parser.add_argument("--ip_to_as", dest='ip_to_as', type=str, help='ip (pfx) to AS db json', default="../pfx2as/data/dbs/2019_10_db.json")
parser.add_argument("--asn_alloc", dest="asn_alloc", type=str, help="ASN allocation file", default="../pfx2as/data/as_allocation/wikipedia_asn_allocation.json")
parser.add_argument("--out_dir", dest="out_dir", type=str, help="output directory", default='.')
parser.add_argument("--ips_per_asn", dest="ips_per_asn", type=int, help="number of high-score IPs to cover an ASN", default=10)
parser.add_argument("--ip_score", dest="ip_score", type=int, help="IP score threshold for pingability", default=90)
parser.add_argument("--asn_coverage", dest="asn_coverage", type=int, help="Coverage of ASNs (percentage)", default=100)
args = parser.parse_args()

assert os.path.isfile(args.pingable_ips)
assert os.path.isfile(args.ip_to_as)
assert os.path.isfile(args.asn_alloc)
out_dir = args.out_dir.rstrip('/')
if not os.path.isdir(out_dir):
    utils.create_dir(out_dir)

print("\t##IMPORTS##")

print("\tImporting DBs:")
print("\t\tIP-to-AS...", end='\r')
ip_to_as_db = lib.dict_list_to_set(lib.import_json(args.ip_to_as))
print("\t\tIP-to-AS...done")

print("\t##PRE-PROCESSING##")

print("\tConverting to Pytricia trees:")
print("\t\tIP-to-AS...", end='\r')
ip_to_as_pyt = lib.convert_json_to_pyt(ip_to_as_db)
print("\t\tIP-to-AS...done")

print("\tCalculating all origin ASes...", end='\r')
all_asns = set()
for prefix in ip_to_as_pyt:
    all_asns.update(ip_to_as_pyt[prefix])
for asn in all_asns:
    assert lib.is_public_asn(asn, asn_allocation_file=args.asn_alloc)
print("\tCalculating all origin ASes...done ({} ASes)".format(len(all_asns)))

print("\tCalculating pingable IPs per ASN...", end='\r')
asn_to_pingable_ips = {}
pingable_ip_to_asn = {}
fully_covered_asns = set()
line_count = 0
high_score_ip_address_count = 0
with bz2.open(args.pingable_ips, 'r') as f:
    for next_line in f:
        line = next_line.decode("utf-8").rstrip("\n")
        line_count += 1
        if line.startswith("#fsdb"):
            continue
        ip_match = re.match("^(\S+)\s*(\S+)\s*(\S+)\s*(\S+)$", line)
        assert ip_match, "Invalid line '{}' in IP hitlist file!".format(line)
        ip_address = ip_match.group(2)
        score = int(ip_match.group(4))
        # print("{} {}".format(score, ip_address))
        if score < args.ip_score:
            continue
        assert lib.is_valid_ip_address(ip_address, kind="ip"), "Invalid IP address '{}'".format(ip_address)
        high_score_ip_address_count += 1
        if high_score_ip_address_count % 10000 == 0:
            print("\tCalculating pingable IPs per AS... ({} lines, {} high-score IP addresses, {}|{} / {} ASes full|>=1 ping IP)".format(
                line_count,
                high_score_ip_address_count,
                len(fully_covered_asns),
                # len(all_asns),
                len(asn_to_pingable_ips),
                round(args.asn_coverage*len(all_asns)/100.0)
            ), end='\r')
        asns = set()
        if ip_address in ip_to_as_pyt:
            asns = ip_to_as_pyt[ip_address]
        if asns and len(asns) == 1:
            asn = list(asns)[0]
            if asn in fully_covered_asns:
                continue
            if asn not in asn_to_pingable_ips:
                asn_to_pingable_ips[asn] = set()
            if len(asn_to_pingable_ips[asn]) < args.ips_per_asn:
                asn_to_pingable_ips[asn].add(ip_address)
                assert ip_address not in pingable_ip_to_asn
                pingable_ip_to_asn[ip_address] = asn
                if len(asn_to_pingable_ips[asn]) == args.ips_per_asn:
                    fully_covered_asns.add(asn)
            if 100.0*len(asn_to_pingable_ips)/len(all_asns) >= args.asn_coverage:
                break
print("\tCalculating pingable IPs per AS... ({} lines, {} high-score IP addresses, {}|{} / {} ASes full|>=1 ping IP)".format(
    line_count,
    high_score_ip_address_count,
    len(fully_covered_asns),
    # len(all_asns),
    len(asn_to_pingable_ips),
    round(args.asn_coverage*len(all_asns)/100.0)
))
# turn to lists to keep scanning order
for asn in asn_to_pingable_ips:
    asn_to_pingable_ips[asn] = list(asn_to_pingable_ips[asn])
utils.dump_json("{}/pingable_ip_to_asn.json".format(out_dir), pingable_ip_to_asn)
utils.dump_json("{}/asn_to_pingable_ips.json".format(out_dir), asn_to_pingable_ips)
