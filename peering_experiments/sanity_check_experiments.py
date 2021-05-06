#!/usr/bin/env python3

import argparse
import glob
import json
import os
import re


def match_single_announcement(sub_dir):
    sub_dir_stripped = sub_dir.split('/')[-1]
    sub_dir_match = re.match("^announce_([a-z]+\d+)_Y\d+_M\d+_D\d+_H\d+_M\d+$", sub_dir_stripped)
    if sub_dir_match:
        matched_mux = sub_dir_match.group(1)
        assert os.path.isdir("{}/control_plane".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/announce_{}.json".format(sub_dir, matched_mux)), sub_dir
        with open("{}/control_plane/announce_{}.json".format(sub_dir, matched_mux), 'r') as f:
            d = json.load(f)
            conf_prefix = list(d.keys())[0]
        assert os.path.isfile("{}/control_plane/asn_to_u_mux.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/asn_to_u_mux_rel.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/available_muxes.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/bird_mux_status.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/exp_configured_muxes.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/live_muxes.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/metadata.json".format(sub_dir)), sub_dir
        with open("{}/control_plane/metadata.json".format(sub_dir), 'r') as f:
            d = json.load(f)
            time_bgpstream_start = d["start_check"]
            time_bgpstream_end = d["end_check"]
        assert os.path.isfile("{}/control_plane/mux_to_origin.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/mux_to_u_asn.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/mux_to_u_asn_rel.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/origin_to_mux.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/peers.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/vpn_mux_status.json".format(sub_dir)), sub_dir
        conf_prefix_net, conf_prefix_netmask = conf_prefix.split("/")
        conf_prefix_octets = conf_prefix_net.split(".")
        assert os.path.isfile("{}/control_plane/bgpstream_paths_for_prefix_{}.{}.{}.{}_{}_{}_{}.csv".format(
            sub_dir,
            conf_prefix_octets[0],
            conf_prefix_octets[1],
            conf_prefix_octets[2],
            conf_prefix_octets[3],
            conf_prefix_netmask,
            time_bgpstream_start,
            time_bgpstream_end
        )), sub_dir
        return (matched_mux,)
    return False


def match_single_withdrawal(sub_dir):
    sub_dir_stripped = sub_dir.split('/')[-1]
    sub_dir_match = re.match("^withdraw_([a-z]+\d+)_Y\d+_M\d+_D\d+_H\d+_M\d+$", sub_dir_stripped)
    if sub_dir_match:
        matched_mux = sub_dir_match.group(1)
        assert os.path.isdir("{}/control_plane".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/withdraw_{}.json".format(sub_dir, matched_mux)), sub_dir
        assert os.path.isfile("{}/control_plane/asn_to_u_mux.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/asn_to_u_mux_rel.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/available_muxes.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/bird_mux_status.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/exp_configured_muxes.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/live_muxes.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/metadata.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/mux_to_origin.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/mux_to_u_asn.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/mux_to_u_asn_rel.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/origin_to_mux.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/peers.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/vpn_mux_status.json".format(sub_dir)), sub_dir
        return (matched_mux,)
    return False


def match_pair_announcement(sub_dir):
    sub_dir_stripped = sub_dir.split('/')[-1]
    sub_dir_match = re.match("^announce_([a-z]+\d+)_([a-z]+\d+)_Y\d+_M\d+_D\d+_H\d+_M\d+$", sub_dir_stripped)
    if sub_dir_match:
        matched_mux_1 = sub_dir_match.group(1)
        matched_mux_2 = sub_dir_match.group(2)
        assert os.path.isfile("{}/{}.json".format(sub_dir, sub_dir_stripped)), sub_dir
        assert os.path.isdir("{}/control_plane".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/announce_{}_{}.json".format(sub_dir, matched_mux_1, matched_mux_2)), sub_dir
        with open("{}/control_plane/announce_{}_{}.json".format(sub_dir, matched_mux_1, matched_mux_2), 'r') as f:
            d = json.load(f)
            conf_prefix = list(d.keys())[0]
        assert os.path.isfile("{}/control_plane/asn_to_u_mux.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/asn_to_u_mux_rel.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/available_muxes.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/bird_mux_status.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/exp_configured_muxes.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/live_muxes.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/metadata.json".format(sub_dir)), sub_dir
        with open("{}/control_plane/metadata.json".format(sub_dir), 'r') as f:
            d = json.load(f)
            time_bgpstream_start = d["start_check"]
            time_bgpstream_end = d["end_check"]
        assert os.path.isfile("{}/control_plane/mux_to_origin.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/mux_to_u_asn.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/mux_to_u_asn_rel.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/origin_to_mux.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/peers.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/vpn_mux_status.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/est_as_to_mux_catchment.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/est_mon_to_mux_catchment.json".format(sub_dir)), sub_dir
        conf_prefix_net, conf_prefix_netmask = conf_prefix.split("/")
        conf_prefix_octets = conf_prefix_net.split(".")
        assert os.path.isfile("{}/control_plane/bgpstream_paths_for_prefix_{}.{}.{}.{}_{}_{}_{}.csv".format(
            sub_dir,
            conf_prefix_octets[0],
            conf_prefix_octets[1],
            conf_prefix_octets[2],
            conf_prefix_octets[3],
            conf_prefix_netmask,
            time_bgpstream_start,
            time_bgpstream_end
        )), sub_dir
        assert os.path.isdir("{}/data_plane".format(sub_dir)), sub_dir
        assert os.path.isdir("{}/data_plane/pings".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/data_plane/pings/asn_to_pingable_ips.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/data_plane/pings/est_as_to_mux_catchment.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/data_plane/pings/pingable_ip_to_asn.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/data_plane/pings/pings_per_asn.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/data_plane/pings/tap_macs.json".format(sub_dir)), sub_dir
        assert os.path.isdir("{}/data_plane/pings/raw".format(sub_dir)), sub_dir
        assert len(glob.glob("{}/data_plane/pings/raw/*.json".format(sub_dir))) > 1000, sub_dir
        assert os.path.isdir("{}/data_plane/traceroutes".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/data_plane/traceroutes/as_level_paths.csv".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/data_plane/traceroutes/est_as_to_last_as_catchment.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/data_plane/traceroutes/est_as_to_mux_catchment.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/data_plane/traceroutes/est_ra_to_last_as_catchment.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/data_plane/traceroutes/est_ra_to_mux_catchment.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/data_plane/traceroutes/msm_info.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/data_plane/traceroutes/prb_info.json".format(sub_dir)), sub_dir
        return (matched_mux_1, matched_mux_2)
    return False


def match_pair_withdrawal(sub_dir):
    sub_dir_stripped = sub_dir.split('/')[-1]
    sub_dir_match = re.match("^withdraw_([a-z]+\d+)_([a-z]+\d+)_Y\d+_M\d+_D\d+_H\d+_M\d+$", sub_dir_stripped)
    if sub_dir_match:
        matched_mux_1 = sub_dir_match.group(1)
        matched_mux_2 = sub_dir_match.group(2)
        assert os.path.isdir("{}/control_plane".format(sub_dir))
        assert os.path.isfile("{}/control_plane/withdraw_{}_{}.json".format(sub_dir, matched_mux_1, matched_mux_2)), sub_dir
        assert os.path.isfile("{}/control_plane/asn_to_u_mux.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/asn_to_u_mux_rel.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/available_muxes.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/bird_mux_status.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/exp_configured_muxes.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/live_muxes.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/metadata.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/mux_to_origin.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/mux_to_u_asn.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/mux_to_u_asn_rel.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/origin_to_mux.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/peers.json".format(sub_dir)), sub_dir
        assert os.path.isfile("{}/control_plane/vpn_mux_status.json".format(sub_dir)), sub_dir
        return (matched_mux_1, matched_mux_2)
    return False


def main():
    parser = argparse.ArgumentParser(description="sanity check over PEERING experiment results")
    parser.add_argument('-b', '--base_dir', dest='base_dir', type=str,
                        help='base directory with results', required=True)
    parser.add_argument('-l', '--list_dirs', dest='list_dirs', type=str,
                        help='json file with experiment directories', default='./list_of_experiment_dirs.json')
    args = parser.parse_args()

    base_dir = args.base_dir.rstrip("/")
    assert os.path.isdir(base_dir)

    assert os.path.isfile(args.list_dirs)
    with open(args.list_dirs, 'r') as f:
        list_of_dirs = json.load(f)

    for exp_dir_stripped in list_of_dirs:
        exp_dir = "{}/{}".format(base_dir, exp_dir_stripped)
        assert os.path.isdir(exp_dir), exp_dir
        dir_name_match = re.match("^(\d+)_([a-z]+\d+)_([a-z]+\d+)$", exp_dir_stripped)
        assert dir_name_match, exp_dir
        mux1 = dir_name_match.group(2)
        mux2 = dir_name_match.group(3)
        mux1_single_announce = False
        mux1_single_withdraw = False
        mux2_single_announce = False
        mux2_single_withdraw = False
        mux1_mux2_pair_announce = False
        mux1_mux2_pair_withdraw = False

        found_sub_dirs = 0
        for sub_dir in glob.glob("{}/*".format(exp_dir)):
            found_sub_dirs += 1
            assert os.path.isdir(sub_dir), sub_dir
            matched_muxes = match_single_announcement(sub_dir)
            if matched_muxes:
                matched_mux = matched_muxes[0]
                assert matched_mux in {mux1, mux2}, sub_dir
                if matched_mux == mux1:
                    mux1_single_announce = True
                elif matched_mux == mux2:
                    mux2_single_announce = True
                continue

            matched_muxes = match_single_withdrawal(sub_dir)
            if matched_muxes:
                matched_mux = matched_muxes[0]
                assert matched_mux in {mux1, mux2}, sub_dir
                if matched_mux == mux1:
                    mux1_single_withdraw = True
                elif matched_mux == mux2:
                    mux2_single_withdraw = True
                continue

            matched_muxes = match_pair_announcement(sub_dir)
            if matched_muxes:
                assert matched_muxes == (mux1, mux2), sub_dir
                mux1_mux2_pair_announce = True
                continue

            matched_muxes = match_pair_withdrawal(sub_dir)
            if matched_muxes:
                assert matched_muxes == (mux1, mux2), sub_dir
                mux1_mux2_pair_withdraw = True
                continue

        assert found_sub_dirs == 6, exp_dir
        assert mux1_single_announce, exp_dir
        assert mux1_single_withdraw, exp_dir
        assert mux2_single_announce, exp_dir
        assert mux2_single_withdraw, exp_dir
        assert mux1_mux2_pair_announce, exp_dir
        assert mux1_mux2_pair_withdraw, exp_dir


if __name__ == "__main__":
    main()








