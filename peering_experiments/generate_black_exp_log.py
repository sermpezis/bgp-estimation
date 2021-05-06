#!/usr/bin/env python3

import glob

with open("exp_log.txt", 'w') as f:
    for i,json_file in enumerate(glob.glob("mux_pair_announcements_jsons/*.json")):
        name = json_file.split('/')[-1].split(".json")[-2]
        muxes = name.split("_")[1:3]
        print(muxes)
        f.write("{}) {} - {} (TBD) --> pending\n".format(i+1, muxes[0], muxes[1]))
        f.write("\t{}.1) {} - announce --> pending\n".format(i+1, muxes[0]))
        f.write("\t{}.2) {} - withdraw --> pending\n".format(i+1, muxes[0]))
        f.write("\t{}.3) {} - announce --> pending\n".format(i+1, muxes[1]))
        f.write("\t{}.4) {} - withdraw --> pending\n".format(i+1, muxes[1]))
        f.write("\t{}.5) {} - {} - announce --> pending\n".format(i+1, muxes[0], muxes[1]))
        f.write("\t{}.5) {} - {} - withdraw --> pending\n".format(i+1, muxes[0], muxes[1]))
