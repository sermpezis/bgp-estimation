#!/usr/bin/env python3

import argparse
import sys
# import pyroute2
import os
import json
# https://stackoverflow.com/questions/23269226/scapy-in-a-script
import scapy.all as scapy
import netaddr
import random
import subprocess
import time

# from pyroute2 import IPRoute

FNULL = open(os.devnull, 'w')

def is_valid_ip(ip):
    try:
        netaddr.IPAddress(ip)
        return True
    except:
        return False
    return False

parser = argparse.ArgumentParser(description="send probe from PEERING towards IP address")
parser.add_argument('-s', "--source_ip", dest='source_ip', type=str,
                    help='source IP address', required=True)
parser.add_argument('-t', "--target_ip", dest='target_ip', type=str,
                     help='target IP address', required=True)
parser.add_argument('-a', "--anycast_taps_mux", dest="anycast_taps_to_muxes", type=str,
                    help="json file with taps and muxes info", required=True)
parser.add_argument("-m", "--mac_taps", dest="mac_taps", type=str,
                    help="json file with tap to macs info", required=True)
parser.add_argument("-d", "--dir_temp", dest="dir_temp", type=str,
                    help="temporary directory for storing intermediate .pcap files", default="tmp")
parser.add_argument("-p", "--probe", dest="probe", type=str, help="probing method", choices=["icmp", "tcp-443"], default="icmp")
parser.add_argument("-o", "--out_dir", dest="out_dir", type=str,
                    help="output directory", default="results")
args = parser.parse_args()

assert is_valid_ip(args.source_ip), "Source IP {} is not valid!".format(args.source_ip)
assert is_valid_ip(args.target_ip), "Target IP {} is not valid!".format(args.target_ip)
tmp_dir = args.dir_temp.rstrip('/')
if not os.path.isdir(tmp_dir):
    os.mkdir(tmp_dir)

out_dir = args.out_dir.rstrip('/')
if not os.path.isdir(out_dir):
    os.mkdir(out_dir)

tap_to_mux = {}
mux_to_tap = {}
with open(args.anycast_taps_to_muxes, 'r') as f:
    d = json.load(f)
    for mux in d:
        if d[mux]["status"] == "up":
            mux_to_tap[mux] = d[mux]["tap"]
            tap_to_mux[d[mux]["tap"]] = mux

tap_macs = {}
with open(args.mac_taps, 'r') as f:
    tap_macs = json.load(f)

all_taps = list(tap_to_mux.keys())
random_tap = random.choice(list(tap_to_mux.keys()))
random_tap_mac = tap_macs[random_tap]

# add the route for the selected IP and tap
#os.system("sudo ip route add {} dev {}".format(args.target_ip, random_tap))
# with IPRoute() as ip:
#     random_tap_ifindex = ip.link_lookup(ifname=random_tap)[0]
#     ip.route("add", dst=args.target_ip, mask=32, oif=random_tap_ifindex)

tcpdump_processes = set()
pcap_files = {}
for capture_tap in all_taps:
    pcap_files[capture_tap] = "{}/p_{}_{}_s{}_d{}_t{}_reply.pcap".format(tmp_dir, args.probe, capture_tap, args.source_ip, args.target_ip, int(time.time()))
    # filter syntax: http://biot.com/capstats/bpf.html
    tcpdump_args = [
        "timeout",
        "3",
        "tcpdump",
        "-ni",
        capture_tap,
        "src",
        "host",
        args.target_ip,
        "and",
        "dst",
        "host",
        args.source_ip,
    ]
    if args.probe == "icmp":
        tcpdump_args.extend([
            "and",
            "icmp",
            "and",
            "icmp[icmptype]",
            "==",
            "0"
        ])
    elif args.probe == "tcp-443":
        tcpdump_args.extend([
            "and",
            "tcp",
            "and",
            "src",
            "port",
            "443"
        ])
    tcpdump_args.extend([
        "-w",
        pcap_files[capture_tap]
    ])
    tcpdump_processes.add(subprocess.Popen(tcpdump_args, stdout=FNULL, stderr=FNULL))

if args.probe == "icmp":
    scapy.sendp(scapy.Ether(dst=random_tap_mac)/scapy.IP(src=args.source_ip, dst=args.target_ip)/scapy.ICMP(), iface=random_tap)
elif args.probe == "tcp-443":
    scapy.sendp(scapy.Ether(dst=random_tap_mac)/scapy.IP(src=args.source_ip, dst=args.target_ip)/scapy.TCP(dport=443, flags="S"), iface=random_tap)
# scapy.sniff(iface=random_tap, filter="src host {} and dst host {}".format(args.target_ip, args.source_ip), prn=lambda x: x.sniffed_on+": "+x.summary())
time.sleep(5)

# remove the route for the selected IP and tap
#os.system("sudo ip route del {} dev {}".format(args.target_ip, random_tap))
# with IPRoute() as ip:
#     random_tap_ifindex = ip.link_lookup(ifname=random_tap)[0]
#     ip.route("del", dst=args.target_ip, mask=32, oif=random_tap_ifindex)

taps_received = set()
for capture_tap in all_taps:
    tap_packets = scapy.rdpcap(pcap_files[capture_tap])
    if tap_packets:
        taps_received.add(capture_tap)
    os.remove(pcap_files[capture_tap])

if taps_received:
    with open("{}/{}.json".format(args.out_dir, args.target_ip), 'w') as f:
        muxes_received = set()
        for tap in taps_received:
            muxes_received.add(tap_to_mux[tap])
        mux_sent = tap_to_mux[random_tap]
        json.dump({
            'sent': mux_sent,
            'received': list(muxes_received)
        }, f)

FNULL.close()
