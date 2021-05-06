#!/usr/bin/env python3

import argparse
import os
import json
import subprocess
import sys
sys.path.insert(0, "../pfx2as")
import ip_to_as_lib as lib
import time
import utils
import shutil

SEND_PEERING_PROBE_DB_SCRIPT = "send_peering_probe_dp.py"
PY3_BIN = "/usr/bin/python3"
PING_PROCESS_TIMEOUT = 10

FNULL = open(os.devnull, 'w')

parser = argparse.ArgumentParser(description="issue pings to pingable IPs per ASN")
parser.add_argument("--ping_ip_to_asn", dest="pingable_ip_to_asn", type=str, help="json with pingable IP to ASN dict", default="./pingable_ip_to_asn.json")
parser.add_argument("--asn_to_ping_ips", dest="asn_to_pingable_ips", type=str, help="json with ASN to pingable IPs dict", default="./asn_to_pingable_ips.json")
parser.add_argument("--ip_to_as", dest='ip_to_as', type=str, help='ip (pfx) to AS db json', default="../pfx2as/data/dbs/2019_10_db.json")
parser.add_argument("--asn_alloc", dest="asn_alloc", type=str, help="ASN allocation file", default="../pfx2as/data/as_allocation/wikipedia_asn_allocation.json")
parser.add_argument("--cp_dir", dest="cp_dir", type=str, help="directory with control-plane information", required=True)
parser.add_argument("--dp_dir", dest="dp_dir", type=str, help="directory with data-plane information", required=True)
parser.add_argument("--parallel_ping_num", dest="parallel_ping_num", type=str, help="number of parallel pings to do", default=50)
parser.add_argument("--source_ip", dest="source_ip", type=str, help="source IP to use for the pings", default="184.164.243.1")
parser.add_argument("--max_ases_ok_ping", dest="max_ases_ok_ping", type=int, help="max number of OK pinged ASes", default=100000)
args = parser.parse_args()

assert os.path.isfile(args.ip_to_as)
assert os.path.isfile(args.asn_alloc)
assert os.path.isfile(args.pingable_ip_to_asn)
assert os.path.isfile(args.asn_to_pingable_ips)
dp_dir = args.dp_dir.rstrip('/')
if not os.path.isdir(dp_dir):
    utils.create_dir(dp_dir)
cp_dir = args.cp_dir.rstrip('/')
assert os.path.isdir(cp_dir)
ping_dir = "{}/pings".format(dp_dir)
if not os.path.isdir(ping_dir):
    os.mkdir(ping_dir)
raw_ping_dir = "{}/raw".format(ping_dir)
if not os.path.isdir(raw_ping_dir):
    os.mkdir(raw_ping_dir)
shutil.copy(args.pingable_ip_to_asn, ping_dir)
shutil.copy(args.asn_to_pingable_ips, ping_dir)
vpn_mux_status_file = "{}/vpn_mux_status.json".format(cp_dir)
assert os.path.isfile(vpn_mux_status_file)

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

print("\tLoading pingable ASes and IPs from files...", end='\r')
pingable_ip_to_asn = utils.load_json(args.pingable_ip_to_asn)
asn_to_pingable_ips = utils.load_json(args.asn_to_pingable_ips)
print("\tLoading pingable ASes and IPs from files...done ({} ASNs, {} IPs)".format(
    len(asn_to_pingable_ips),
    len(pingable_ip_to_asn)
))

print("\t##RP FILTER DISABLE###")
print("\tDisabling RP filtering on all and taps...", end='\r')
tap_to_mux = {}
mux_to_tap = {}
with open(vpn_mux_status_file, 'r') as f:
    d = json.load(f)
    for mux in d:
        if d[mux]["status"] == "up":
            mux_to_tap[mux] = d[mux]["tap"]
            tap_to_mux[d[mux]["tap"]] = mux
all_taps = list(tap_to_mux.keys())

with open("/proc/sys/net/ipv4/conf/all/rp_filter", 'w') as f:
    subprocess.call(
        [
            "echo",
            "2"
        ],
        stdout=f,
        stderr=FNULL
)
for tap in all_taps:
    with open("/proc/sys/net/ipv4/conf/{}/rp_filter".format(tap), 'w') as f:
        subprocess.call(
            [
                "echo",
                "2",
            ],
            stdout=f,
            stderr=FNULL
    )
print("\tDisabling RP filtering on all and taps...done")

print("\t##TAP MACS##")
tap_macs = {}
arp_output = subprocess.check_output(["arp"]).decode('utf-8').split('\n')
for arp_line in arp_output:
    arp_elems_w_blanks = list(map(lambda x: x.strip(" "), arp_line.split(" ")))
    arp_elems_wo_blanks = []
    for arp_elem_w_blanks in arp_elems_w_blanks:
        if arp_elem_w_blanks != "":
            arp_elems_wo_blanks.append(arp_elem_w_blanks)
    if len(arp_elems_wo_blanks) == 5 and arp_elems_wo_blanks[4] in all_taps and arp_elems_wo_blanks[0] != args.source_ip:
        tap_macs[arp_elems_wo_blanks[4]] = arp_elems_wo_blanks[2]

assert(len(tap_macs) == len(all_taps))
tap_macs_file = "{}/tap_macs.json".format(ping_dir)
utils.dump_json(tap_macs_file, tap_macs)

print("\t##MEASUREMENTS##")

print("\tPinging pingable ASes...")

# All IP pings that can be done (will be reduced if an AS has been pinged successfully)
possible_ip_pings = len(pingable_ip_to_asn)

# Other parameters
done_ip_pings = 0
success_ip_pings = 0
asns_pinged_successfully = set()
ping_process_buffer = {}
all_asns_with_pingable_ips_list = list(asn_to_pingable_ips.keys())
ip_index = -1
run = 0
additional_run_required = True

# execute next run (always one in the beginning)
while additional_run_required:
    additional_run_required = False
    run += 1
    ip_index += 1
    asn_index = 0
    # scan all ASes
    while asn_index <= len(all_asns_with_pingable_ips_list) - 1:
        # get next AS
        asn = all_asns_with_pingable_ips_list[asn_index]
        asn_index += 1

        if asn not in asns_pinged_successfully:
            # if not pinged successfully but do not have spare IPs, ignore
            if ip_index > len(asn_to_pingable_ips[asn]) - 1:
                continue
            next_pingable_ip = asn_to_pingable_ips[asn][ip_index]
            ping_process = [
                "timeout",
                str(PING_PROCESS_TIMEOUT),
                PY3_BIN,
                SEND_PEERING_PROBE_DB_SCRIPT,
                '-s',
                args.source_ip,
                '-t',
                next_pingable_ip,
                '-a',
                vpn_mux_status_file,
                '-m',
                tap_macs_file,
                '-p',
                "icmp",
                '-o',
                raw_ping_dir
            ]
            ping_process_buffer[next_pingable_ip] = (asn, subprocess.Popen(ping_process, stdout=FNULL, stderr=FNULL))
            done_ip_pings += 1
            assert len(ping_process_buffer) <= args.parallel_ping_num
            print("\tRUN {}, CURRENT || IP PINGS {}, TOTAL IP PINGS {}, SUCCESS IP PINGS {}, SUCCESS AS PINGS {}/{}, PROGRESS {}%...\t\t".format(
                run,
                len(ping_process_buffer),
                done_ip_pings,
                success_ip_pings,
                len(asns_pinged_successfully),
                args.max_ases_ok_ping,
                round(100.0*done_ip_pings/possible_ip_pings, 2)), end='\r')
            if len(ping_process_buffer) == args.parallel_ping_num:
                time.sleep(PING_PROCESS_TIMEOUT + 1)
                pinged_ips_to_delete = set()
                for pinged_ip in ping_process_buffer:
                    pinged_asn = ping_process_buffer[pinged_ip][0]
                    result_json = "{}/{}.json".format(raw_ping_dir, pinged_ip)
                    if os.path.isfile(result_json):
                        if pinged_asn not in asns_pinged_successfully:
                            possible_ip_pings -= len(asn_to_pingable_ips[pinged_asn]) - (ip_index + 1)
                            asns_pinged_successfully.add(pinged_asn)
                        success_ip_pings += 1
                        if len(asns_pinged_successfully) >= args.max_ases_ok_ping:
                            break
                    else:
                        additional_run_required = True
                    pinged_ips_to_delete.add(pinged_ip)
                for pinged_ip in pinged_ips_to_delete:
                    del ping_process_buffer[pinged_ip]
            if len(asns_pinged_successfully) >= args.max_ases_ok_ping:
                break

    if len(asns_pinged_successfully) >= args.max_ases_ok_ping:
        break

    while len(ping_process_buffer) > 0:
        time.sleep(PING_PROCESS_TIMEOUT + 1)
        pinged_ips_to_delete = set()
        for pinged_ip in ping_process_buffer:
            pinged_asn = ping_process_buffer[pinged_ip][0]
            result_json = "{}/{}.json".format(raw_ping_dir, pinged_ip)
            if os.path.isfile(result_json):
                if pinged_asn not in asns_pinged_successfully:
                    possible_ip_pings -= len(asn_to_pingable_ips[pinged_asn]) - (ip_index + 1)
                    asns_pinged_successfully.add(pinged_asn)
                success_ip_pings += 1
            else:
                additional_run_required = True
            pinged_ips_to_delete.add(pinged_ip)
            print("\tRUN {}, CURRENT || IP PINGS {}, TOTAL IP PINGS {}, SUCCESS IP PINGS {}, SUCCESS AS PINGS {}/{}, PROGRESS {}%...\t\t".format(
                run,
                len(ping_process_buffer),
                done_ip_pings,
                success_ip_pings,
                len(asns_pinged_successfully),
                args.max_ases_ok_ping,
                round(100.0*done_ip_pings/possible_ip_pings, 2)), end='\r')
        for pinged_ip in pinged_ips_to_delete:
            del ping_process_buffer[pinged_ip]

print("\tRUN {}, CURRENT || IP PINGS {}, TOTAL IP PINGS {}, SUCCESS IP PINGS {}, SUCCESS AS PINGS {}/{}, PROGRESS {}%...done\t\t".format(
    run,
    len(ping_process_buffer),
    done_ip_pings,
    success_ip_pings,
    len(asns_pinged_successfully),
    args.max_ases_ok_ping,
    round(100.0*done_ip_pings/possible_ip_pings, 2)))

FNULL.close()
