#!/usr/bin/env python3

import argparse
import os
import subprocess
import  time

PY3_BIN = '/usr/bin/python3'
RUN_PEERING_EXP_PY = 'run_peering_exp.py'
SAFE_WAIT = 10*60 # wait for 10 minutes before proceeding

parser = argparse.ArgumentParser(description="run full peering experiment for a given pair of muxes")
parser.add_argument("--m1", dest='mux_1', type=str, help='mux 1', required=True)
parser.add_argument("--m2", dest='mux_2', type=str, help='mux 2', required=True)
args = parser.parse_args()

for mux in [args.mux_1, args.mux_2]:
    assert os.path.isfile("mux_announcements_jsons/announce_{}.json".format(mux))
    assert os.path.isfile("mux_withdrawals_jsons/withdraw_{}.json".format(mux))
assert os.path.isfile("mux_pair_announcements_jsons/announce_{}_{}.json".format(args.mux_1, args.mux_2))
assert os.path.isfile("mux_pair_withdrawals_jsons/withdraw_{}_{}.json".format(args.mux_1, args.mux_2))

print("Experiment started...")
print("Safe waiting for 10 minutes...")
time.sleep(SAFE_WAIT)

for mux in [args.mux_1, args.mux_2]:

    print("Announcing only from {} to get BGPStream paths...".format(mux))
    cmd_list = [
        PY3_BIN,
        RUN_PEERING_EXP_PY,
        "-e", "mux_announcements_jsons/announce_{}.json".format(mux),
        "-b"
    ]
    cmd_str = ' '.join(cmd_list)
    print('\tRunning: {}'.format(cmd_str))
    subprocess.run(cmd_list)
    print("Announcing only from {} to get BGPStream paths...done".format(mux))
    print("Safe waiting for 10 minutes...")
    time.sleep(SAFE_WAIT)

    print("Withdrawing only from {}...".format(mux))
    cmd_list = [
        PY3_BIN,
        RUN_PEERING_EXP_PY,
        "-e", "mux_withdrawals_jsons/withdraw_{}.json".format(mux),
    ]
    cmd_str = ' '.join(cmd_list)
    print('\tRunning: {}'.format(cmd_str))
    subprocess.run(cmd_list)
    print("Withdrawing only from {}...done".format(mux))
    print("Safe waiting for 10 minutes...")
    time.sleep(SAFE_WAIT)

print("Announcing both from {} and {} to get pings, traceroutes and BGPStream paths...".format(args.mux_1, args.mux_2))
cmd_list = [
    PY3_BIN,
    RUN_PEERING_EXP_PY,
    "-e", "mux_pair_announcements_jsons/announce_{}_{}.json".format(args.mux_1, args.mux_2),
    "-a",
    "-t",
    "-d",
    "-b"
]
cmd_str = ' '.join(cmd_list)
print('\tRunning: {}'.format(cmd_str))
subprocess.run(cmd_list)
print("Announcing both from {} and {} to get pings, traceroutes and BGPStream paths...done".format(args.mux_1, args.mux_2))
print("Safe waiting for 10 minutes...")
time.sleep(SAFE_WAIT)

print("Withdrawing both from {} and {}...".format(args.mux_1, args.mux_2))
cmd_list = [
    PY3_BIN,
    RUN_PEERING_EXP_PY,
    "-e", "mux_pair_withdrawals_jsons/withdraw_{}_{}.json".format(args.mux_1, args.mux_2)
]
cmd_str = ' '.join(cmd_list)
print('\tRunning: {}'.format(cmd_str))
subprocess.run(cmd_list)
print("Withdrawing both from {} and {}...done".format(args.mux_1, args.mux_2))
print("Safe waiting for 10 minutes...")
time.sleep(SAFE_WAIT)

print("Experiment completed")
