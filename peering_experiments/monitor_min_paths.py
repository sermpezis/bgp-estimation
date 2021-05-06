import argparse
import csv
import os

PEERING_ORIGIN = 47065


class AS_path:
    """
    AS path cleaning and length computation
    """
    def make_list(self, AS_PATH):
        """
        Give an AS_PATH as a string in the following format : AS1,AS2,AS3,AS3 , returns a list 
        that contains the ASes found in the as_path

        Input: AS_PATH (string)
        Output: list of positive integers
        """
        return map(int,AS_PATH.split(','))


    def remove_prependings(self, AS_PATH):
        """
        Returns a list of the ASes in the AS_PATH, in the same order they can be found
        in the original one, but prependings have been removed.

        Input: AS_PATH (list of positive integers) 
        Output: cleaned list
        """
        as_list = []
        for as_ in AS_PATH:
            if as_ != '' and as_ not in as_list:
                as_list.append(as_)
        return as_list

    def remove_loops(self, AS_PATH):
        """
        Cleans loops that are found in the AS_PATH as result of BGP poisoning

        Input: AS_PATH (list of positive integers) 
        Output: cleared list

        """
        seq_inv = AS_PATH[::-1]
        new_seq_inv = []
        for x in seq_inv:
            if x not in new_seq_inv:
                new_seq_inv.append(x)
            else:
                x_index = new_seq_inv.index(x)
                new_seq_inv = new_seq_inv[: x_index + 1]
        return new_seq_inv[::-1]


    def count_length(self, AS_PATH, origin_as):
        """
        Returns the length of AS_PATH until  origin_as

        e.g. Given origin_as 47065:    
        4608,7575,11537,101,47065,1111 -> length = 5

        Input: AS_PATH (list of positive integers)  list cleaned from poisoning an prependings
               origin_as (positive integer): the asn till which we count the length of
               the path. Acts as the terminal as.

        Output the length of the as_path if the given origin as found in the as path. Otherwise -1 is returned.
        """
        length = 0

        for i in range(len(AS_PATH)):
            length+=1
            if AS_PATH[i] == origin_as:
                return length

        return 9999 # cost of not having the origin_as in the as_Path -> very big length: probably not chosen



def compute_min_paths_from_monitors(csv_file_path, delimiter='\t', origin_as=PEERING_ORIGIN):
    """
    Inputs:  csv_file_path, delimiter : csv file containing entries with the following format:
             |collector|monitor|as_path, and the delimiter used

             origin_as: the ASN you want to use as the terminal one for the as_path length computation

    Output:  A dictionary that contains for each monitor found in the given csv file, the minimum length path
             and its length.

    """

    monitor_routes = {} # contains the minimum length found for each route monitor
                          # key:monitor(string), value: (minimum as_path length(integer),
                          # the minimum length as_path(list of positive integers))

    with open(csv_file_path) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=delimiter)

        row_count = 0
        for row in csv_reader:
            row_count += 1
            monitor = row[1]
            # AS-path prep removing prepending and bgp poisoning
            as_path_list = AS_path().make_list(row[2]) # as_path(string) -> as_path (list of positive integers)
            as_path_rem_prepend = AS_path().remove_prependings(as_path_list)
            as_path_cleared = AS_path().remove_loops(as_path_rem_prepend)
            as_path_length = AS_path().count_length(as_path_cleared, origin_as)

            if monitor in monitor_routes.keys():
                if monitor_routes[monitor][0] > as_path_length:
                    monitor_routes[monitor] = (as_path_length, as_path_cleared)
            else:
                monitor_routes[monitor] = (as_path_length, as_path_cleared)

    return monitor_routes


def create_min_paths_csv(monitors_dict, outfile):
    with open(outfile, 'w') as writeFile:
        writer = csv.writer(writeFile, delimiter='\t')
        for monitor in monitors_dict:
            min_length = monitors_dict[monitor][0]
            path = monitors_dict[monitor][1]
            writer.writerow([monitor, min_length, ','.join(map(str, path))])


parser = argparse.ArgumentParser(description="calculate path lengths per monitor")
parser.add_argument('-b', '--bgpstream_paths', dest='bgpstream_paths_file', type=str,
                    help='file with bgpstream-seen paths towards anycasters', required=True)
parser.add_argument('-c', '--cp', dest='cp_dir', type=str,
                    help='directory with control-plane information', required=True)
args = parser.parse_args()

assert os.path.isfile(args.bgpstream_paths_file)
cp_dir = args.cp_dir.rstrip('/')
mps = compute_min_paths_from_monitors(args.bgpstream_paths_file)
create_min_paths_csv(mps, "{}/mon_path_lengths.csv".format(cp_dir))
