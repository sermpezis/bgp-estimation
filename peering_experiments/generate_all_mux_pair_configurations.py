#!/usr/bin/env python3

import argparse
import os
import utils

PEERING_PREFIX = "184.164.243.0/24"
PRIVATE_ORIGINS = [61574, 61575]
PEERING_ASN = 47065

parser = argparse.ArgumentParser(description="produce all pairwise experiment configurations")
parser.add_argument('-m', '--muxes', dest='muxes', type=str,
                    help='json file with mux list', default="./valid_muxes.json")
parser.add_argument('-o', '--out_dir', dest='out_dir', type=str,
                    help='output directory', required=True)
parser.add_argument('-t', '--type', dest='exp_type', choices=['A', 'W'],
                    help='type of experiment', required=True)
args = parser.parse_args()

out_dir = args.out_dir.rstrip('/')
if not os.path.isdir(out_dir):
    utils.create_dir(out_dir)
assert os.path.isfile(args.muxes)
muxes = utils.load_json(args.muxes)

seen_pairs = set()
for mux_1 in muxes:
    for mux_2 in muxes:
        if mux_1 != mux_2:
            mux_pair = "{}-{}".format(mux_1, mux_2)
            rev_mux_pair = "{}-{}".format(mux_2, mux_1)
            if mux_pair not in seen_pairs and rev_mux_pair not in seen_pairs:
                if args.exp_type == 'A':
                    exp_conf = {
                        PEERING_PREFIX: {
                            "announce": [
                                {
                                    "muxes": [
                                        mux_1
                                    ],
                                    "origin": PEERING_ASN,
                                    "prepend": [PRIVATE_ORIGINS[0]]
                                },
                                {
                                    "muxes": [
                                        mux_2
                                    ],
                                    "origin": PEERING_ASN,
                                    "prepend": [PRIVATE_ORIGINS[1]]
                                }
                            ]
                        }
                    }
                    utils.dump_json("{}/announce_{}_{}.json".format(out_dir, mux_1, mux_2), exp_conf, indent=2)
                elif args.exp_type == 'W':
                    exp_conf = {
                        PEERING_PREFIX: {
                            "withdraw": [
                                mux_1,
                                mux_2
                            ]
                        }
                    }
                    utils.dump_json("{}/withdraw_{}_{}.json".format(out_dir, mux_1, mux_2), exp_conf, indent=2)
                seen_pairs.add(mux_pair)
