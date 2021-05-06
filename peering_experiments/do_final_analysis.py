#!/usr/bin/env python3

import argparse
import json
import glob
import os
import re
import subprocess
import shutil

PY3_BIN = '/usr/bin/python3'
TRACE_TRANS_PY = 'translate_traceroutes_to_catchment.py'
DP_PROBE_TRANS_PY = 'translate_dp_probes_to_catchment.py'
BGPSTREAM_TRANS_PY = 'translate_bgpstream_paths_to_catchment.py'

parser = argparse.ArgumentParser(description="redo analysis over PEERING experiment results")
parser.add_argument('-b', '--base_dir', dest='base_dir', type=str,
                    help='base directory with results', required=True)
parser.add_argument('-l', '--list_dirs', dest='list_dirs', type=str,
                    help='json file with experiment directories', default='./list_of_experiment_dirs.json')
parser.add_argument('-o', '--out_dir', dest='out_dir', type=str,
                    help="output directory with final results", required=True)
parser.add_argument('-i', '--ip_to_as', dest='ip_to_as', type=str,
                    help='ip (pfx) to AS db json', default="../pfx2as/data/dbs/2019_10_db.json")
args = parser.parse_args()

base_dir = args.base_dir.rstrip("/")
assert os.path.isdir(base_dir)

assert os.path.isfile(args.list_dirs)
with open(args.list_dirs, 'r') as f:
    list_of_dirs = json.load(f)

out_dir = args.out_dir.rstrip("/")
if not os.path.isdir(out_dir):
    os.mkdir(out_dir)

for exp_dir_stripped in list_of_dirs:
    print("Analyzing {}...".format(exp_dir_stripped))
    exp_dir = "{}/{}".format(base_dir, exp_dir_stripped)
    assert os.path.isdir(exp_dir), exp_dir
    dir_name_match = re.match("^(\d+)_([a-z]+\d+)_([a-z]+\d+)$", exp_dir_stripped)
    assert dir_name_match, exp_dir
    exp_id = dir_name_match.group(1)
    mux1 = dir_name_match.group(2)
    mux2 = dir_name_match.group(3)
    out_sub_dir = "{}/{}_{}_{}".format(
        out_dir,
        exp_id,
        mux1,
        mux2
    )
    assert not os.path.isdir(out_sub_dir)
    os.mkdir(out_sub_dir)

    for announce_exp_sub_dir in glob.glob("{}/announce_*".format(exp_dir)):
        match = False
        announce_exp_sub_dir_stripped = announce_exp_sub_dir.split('/')[-1]
        single_mux_match = re.match("^announce_([a-z]+\d+)_Y\d+_M\d+_D\d+_H\d+_M\d+$", announce_exp_sub_dir_stripped)
        if single_mux_match:
            matched_mux = single_mux_match.group(1)
            assert matched_mux in {mux1, mux2}
            print("\tAnalyzing single announcement {}...".format(announce_exp_sub_dir))
            with open("{}/control_plane/announce_{}.json".format(announce_exp_sub_dir, matched_mux), 'r') as f:
                d = json.load(f)
                conf_prefix = list(d.keys())[0]
            with open("{}/control_plane/metadata.json".format(announce_exp_sub_dir), 'r') as f:
                d = json.load(f)
                time_bgpstream_start = d["start_check"]
                time_bgpstream_end = d["end_check"]
            conf_prefix_net, conf_prefix_netmask = conf_prefix.split("/")
            conf_prefix_octets = conf_prefix_net.split(".")
            shutil.copy(
                "{}/control_plane/bgpstream_paths_for_prefix_{}.{}.{}.{}_{}_{}_{}.csv".format(
                    announce_exp_sub_dir,
                    conf_prefix_octets[0],
                    conf_prefix_octets[1],
                    conf_prefix_octets[2],
                    conf_prefix_octets[3],
                    conf_prefix_netmask,
                    time_bgpstream_start,
                    time_bgpstream_end
                ),
                "{}/{}".format(
                    out_sub_dir,
                    "{}_bgpstream_paths.csv".format(
                        matched_mux,
                        conf_prefix_octets[0],
                        conf_prefix_octets[1],
                        conf_prefix_octets[2],
                        conf_prefix_octets[3],
                        conf_prefix_netmask,
                        time_bgpstream_start,
                        time_bgpstream_end
                    )
                )
            )
            print("\tAnalyzing single announcement {}...done".format(announce_exp_sub_dir))
            match = True
            continue

        mux1_2_match = re.match("^announce_{}_{}_Y\d+_M\d+_D\d+_H\d+_M\d+$".format(mux1, mux2), announce_exp_sub_dir_stripped)
        if mux1_2_match:
            print("\tAnalyzing pair announcement {}...".format(announce_exp_sub_dir))
            with open("{}/control_plane/announce_{}_{}.json".format(announce_exp_sub_dir, mux1, mux2), 'r') as f:
                d = json.load(f)
                conf_prefix = list(d.keys())[0]
            with open("{}/control_plane/metadata.json".format(announce_exp_sub_dir), 'r') as f:
                d = json.load(f)
                time_bgpstream_start = d["start_check"]
                time_bgpstream_end = d["end_check"]
            conf_prefix_net, conf_prefix_netmask = conf_prefix.split("/")
            conf_prefix_octets = conf_prefix_net.split(".")
            shutil.copy(
                "{}/control_plane/bgpstream_paths_for_prefix_{}.{}.{}.{}_{}_{}_{}.csv".format(
                    announce_exp_sub_dir,
                    conf_prefix_octets[0],
                    conf_prefix_octets[1],
                    conf_prefix_octets[2],
                    conf_prefix_octets[3],
                    conf_prefix_netmask,
                    time_bgpstream_start,
                    time_bgpstream_end
                ),
                "{}/{}".format(
                    out_sub_dir,
                    "{}_{}_bgpstream_paths.csv".format(
                        mux1,
                        mux2,
                        conf_prefix_octets[0],
                        conf_prefix_octets[1],
                        conf_prefix_octets[2],
                        conf_prefix_octets[3],
                        conf_prefix_netmask,
                        time_bgpstream_start,
                        time_bgpstream_end
                    )
                )
            )

            print("\t\tAnalyzing traceroutes...")
            cmd_list = [
                PY3_BIN, TRACE_TRANS_PY,
                '-i', args.ip_to_as,
                '-c', "{}/control_plane".format(announce_exp_sub_dir),
                '-d', "{}/data_plane".format(announce_exp_sub_dir)
            ]
            cmd_str = ' '.join(cmd_list)
            subprocess.run(cmd_list)
            shutil.copy(
                "{}/data_plane/traceroutes/est_ra_to_mux_catchment.json".format(announce_exp_sub_dir),
                "{}/dp_trace_est_ra_as_to_mux_catchment.json".format(out_sub_dir)
            )

            print("\t\tAnalyzing data plane probes...")
            cmd_list = [
                PY3_BIN, DP_PROBE_TRANS_PY,
                '-c', "{}/control_plane".format(announce_exp_sub_dir),
                '-d', "{}/data_plane".format(announce_exp_sub_dir)
            ]
            cmd_str = ' '.join(cmd_list)
            subprocess.run(cmd_list)
            shutil.copy(
                "{}/data_plane/pings/est_as_to_mux_catchment.json".format(announce_exp_sub_dir),
                "{}/dp_pings_est_as_to_mux_catchment.json".format(out_sub_dir)
            )
            shutil.copy(
                "{}/data_plane/pings/pings_per_asn.json".format(announce_exp_sub_dir),
                "{}/dp_pings_per_asn.json".format(out_sub_dir)
            )

            print('\t\tAnalyzing bgpstream paths...')
            bgpstream_file = "{}/control_plane/bgpstream_paths_for_prefix_{}.{}.{}.{}_{}_{}_{}.csv".format(
                announce_exp_sub_dir,
                conf_prefix_octets[0],
                conf_prefix_octets[1],
                conf_prefix_octets[2],
                conf_prefix_octets[3],
                conf_prefix_netmask,
                time_bgpstream_start,
                time_bgpstream_end
            )
            shutil.copy(
                bgpstream_file,
                "{}/{}".format(
                    out_sub_dir,
                    "{}_{}_bgpstream_paths.csv".format(
                        mux1,
                        mux2,
                        conf_prefix_octets[0],
                        conf_prefix_octets[1],
                        conf_prefix_octets[2],
                        conf_prefix_octets[3],
                        conf_prefix_netmask,
                        time_bgpstream_start,
                        time_bgpstream_end
                    )
                )
            )
            cmd_list = [
                PY3_BIN, BGPSTREAM_TRANS_PY,
                '-b', bgpstream_file,
                '-c', "{}/control_plane".format(announce_exp_sub_dir)
            ]
            cmd_str = ' '.join(cmd_list)
            subprocess.run(cmd_list)
            shutil.copy(
                "{}/control_plane/est_mon_to_mux_catchment.json".format(announce_exp_sub_dir),
                "{}/cp_bgpstream_est_mon_as_to_mux_catchment.json".format(out_sub_dir)
            )
            print("\tAnalyzing pair announcement {}...done".format(announce_exp_sub_dir))
            match = True
            continue

        assert match










