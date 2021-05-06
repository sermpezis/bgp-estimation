#!/usr/bin/env python


import argparse
import csv
from _pybgpstream import BGPStream, BGPRecord, BGPElem
import sys
import time

from pprint import pprint as pp


WRITE_DATA_EVERY_N_ROWS = 100


# input arguments
parser = argparse.ArgumentParser(description="fetch bgpstream paths (by RIB reconstruction via BGP updates) for a certain prefix")
parser.add_argument('-p', '--prefix', dest='prefix', type=str,
                    help='prefix to collect AS-paths towards', required=True)
parser.add_argument('-s', '--start', dest='start_time', type=int,
                    help='start time (UNIX epochs)', required=True)
parser.add_argument('-e', '--end', dest='end_time', type=int,
                    help='end time (UNIX epochs)', required=True)
parser.add_argument('-c', '--cp', dest='cp_dir', type=str,
                    help='directory with control-plane information', required=True)
args = parser.parse_args()

prefix = args.prefix
start_time = args.start_time
end_time = args.end_time
cp_dir = args.cp_dir.rstrip('/')
output_filename = '{}/bgpstream_paths_for_prefix_{}_{}_{}_{}.csv'.format(
    cp_dir,
    prefix[0:-3],
    prefix[-2:],
    start_time,
    end_time)

# create a new bgpstream instance and a reusable bgprecord instance
stream = BGPStream()
rec = BGPRecord()

# consider collectors from routeviews and ris
stream.add_filter('project','routeviews')
stream.add_filter('project','ris')

# consider RIBs dumps only
stream.add_filter('record-type', 'updates')

# filter prefix
stream.add_filter('prefix', prefix)

stream.add_interval_filter(int(start_time),int(end_time))

# start the stream
stream.start()

# record start time
time_start = time.time()

# initialize RIBs
ribs = {}

# populate RIBs
while stream.get_next_record(rec):

    if (rec.status != "valid") or (rec.type != "update"):
        continue

    try:
        elem = rec.get_next_elem()
    except:
        print('Cannot retrieve next element!')
        continue

    # print('---')
    # print rec.project, rec.collector, rec.type, rec.time, rec.status
    # print('---')

    while elem:
        if elem.peer_asn not in ribs:
            ribs[elem.peer_asn] = {}
        if rec.collector not in ribs[elem.peer_asn]:
            ribs[elem.peer_asn][rec.collector] = {
                'path': None,
                'timestamp': 0
            }
        # handle announcements
        if elem.type == 'A':
            if ribs[elem.peer_asn][rec.collector]['timestamp'] < rec.time:
                ribs[elem.peer_asn][rec.collector] = {
                    'path': str(",".join(elem.fields['as-path'].split(" "))),
                    'timestamp': rec.time
                }
        # handle withdrawals
        elif elem.type == 'W':
            if ribs[elem.peer_asn][rec.collector]['timestamp'] < rec.time:
                ribs[elem.peer_asn][rec.collector] = {
                    'path': None,
                    'timestamp': rec.time
                }

        try:
            elem = rec.get_next_elem()
        except:
            print('Cannot retrieve next element!')
            continue

# dump RIBs
DATA = []
with open(output_filename, 'a+') as csvfile:
    writer = csv.writer(csvfile, delimiter='\t')

    for asn in ribs:
        for collector in ribs[asn]:
            if ribs[asn][collector]['path'] is not None:
                DATA.append(
                    [
                        collector,
                        asn,
                        ribs[asn][collector]['path']
                    ]
                )

                if len(DATA) == WRITE_DATA_EVERY_N_ROWS:
                    writer.writerows(DATA)
                    DATA = []

    if len(DATA) > 0:
        writer.writerows(DATA)

# record end time
time_end = time.time()
print("Total time required = {} sec".format(time_end - time_start))
