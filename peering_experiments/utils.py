import csv
import json
import os
import random
import re
import subprocess
from datetime import datetime, timedelta
from netaddr import IPNetwork, IPAddress
from ripe.atlas.cousteau import (
    ProbeRequest,
    Traceroute,
    AtlasCreateRequest,
    AtlasResultsRequest,
    AtlasSource
)


SUPPORTED_PEER_FIELDS = [
    "BGP Mux",
    "Peer organization",
    "Peer ASN",
    "Peer IP address",
    "IP version",
    "Short description",
    "Transit",
    "Route Server",
    "Session ID"
]


def map_origin_asn_to_mux(exp_file):
    exp_info = load_json(exp_file)
    mux_to_origin = {}
    origin_to_mux = {}
    for prefix in exp_info:
        if "announce" in exp_info[prefix]:
            for announce_elem in exp_info[prefix]["announce"]:
                if "prepend" in announce_elem:
                    for mux in announce_elem["muxes"]:
                        if mux not in mux_to_origin:
                            mux_to_origin[mux] = set()
                        mux_to_origin[mux].add(announce_elem["prepend"][0])
                        if announce_elem["prepend"][0] not in origin_to_mux:
                            origin_to_mux[announce_elem["prepend"][0]] = set()
                        origin_to_mux[announce_elem["prepend"][0]].add(mux)
    for mux in mux_to_origin:
        mux_to_origin[mux] = list(mux_to_origin[mux])
    for origin in origin_to_mux:
        origin_to_mux[origin] = list(origin_to_mux[origin])
    return (mux_to_origin, origin_to_mux)


def translate_to_pyasn(caida_ip_to_as_file, pyasn_file):
    with open(pyasn_file, 'w') as fout:
        csv_writer = csv.writer(fout, delimiter='\t')
        with open(caida_ip_to_as_file, 'r') as fin:
            csv_reader = csv.reader(fin, delimiter='\t')
            for row in csv_reader: # row[0]: prefix, row[1]: prefix length, row[2]: origin AS(es)
                # discard AS sets and MOAS ASes
                if ('_' not in row[2]) and (',' not in row[2]):
                    prefix = row[0] + '/' + row[1]
                    csv_writer.writerow([prefix, row[2]])


def fetch_msm_result(msm_id):
    kwargs = {
        "msm_id": int(msm_id),
    }
    is_success, results = AtlasResultsRequest(**kwargs).create()
    if is_success:
        return results
    else:
        print("Error while fetching msm: " + str(msm_id))
    return None


def issue_traceroute_msms(probes_list, target_ip, time_offset, api_key):
    description = "Traceroute towards {}".format(target_ip)
    start_time = datetime.utcnow() + timedelta(seconds=int(time_offset))

    data = {
        'definitions': {
            'af': 4,
            'paris': 1,
            'protocol': 'ICMP',
            'type': 'traceroute',
            'target': target_ip,
            'is_oneoff': True,
            'description': description
        },
        'probes': {
            'requested': len(probes_list),
            'type': 'probes',
            'value': ','.join(map(str, probes_list))
        }
    }

    traceroute = Traceroute(** data['definitions'])
    source = AtlasSource(** data['probes'])

    atlas_request = AtlasCreateRequest(
        start_time=start_time,
        key=api_key,
        measurements=[traceroute],
        sources=[source],
        is_oneoff=True
    )

    (is_success, response) = atlas_request.create()

    if is_success:
        print("{}: Success".format(description))
        return response['measurements'][0]
    else:
        print("{}: Failed".format(description))

    return None


def is_valid_prefix(prefix):
    '''
    Check validity of given prefix

    :param prefix: string X.Y.W.Z/N
    :return: <bool> whether the prefix is valid or not
    '''
    try:
        ipnet = IPNetwork(prefix)
    except:
        return False

    return True


def is_valid_ip(ip):
    '''
    Check validity of given IP address

    :param prefix: string X.Y.W.Z
    :return: <bool> whether the ip is valid or not
    '''
    try:
        ipaddr = IPAddress(ip)
    except:
        return False

    return True


def create_dir(dir):
    if not os.path.isdir(dir):
        os.mkdir(dir)


def fetch_probe_info():
    probe_info = {}
    filters = {
        "status": 1,
        "is_public": True,
        "tags": ['system-ipv4-works'] #, 'system-ipv4-stable-30d', 'system-ipv4-stable-1d']
        #"country_code": "GR" # only for testing!
    }
    probes = ProbeRequest(**filters)
    for probe in probes:
        if probe['asn_v4'] is not None:
            probe_info[probe["id"]] = probe
    return probe_info


def map_asns_to_probe_ids(probe_info):
    asns_to_probe_ids = {}
    for probe_id in probe_info:
        asn = probe_info[probe_id]['asn_v4']
        if asn not in asns_to_probe_ids:
            asns_to_probe_ids[asn] = set()
        asns_to_probe_ids[asn].add(probe_id)
    return asns_to_probe_ids


def keep_max_prb_per_asn(asns_to_probe_ids, max_prb_cnt=5):
    for asn in asns_to_probe_ids:
        if len(asns_to_probe_ids[asn]) > max_prb_cnt:
            asns_to_probe_ids[asn] = set(random.sample(list(asns_to_probe_ids[asn]), max_prb_cnt))

def cleanup_exp_state(muxes):
    # bring down bird sessions on the muxes
    control_mux_bird(up=False)

    # bring down all VPN mux tunnels
    control_mux_tun(muxes, up=False)


def control_mux_tun(muxes, up=True):
    state = 'up'
    if not up:
        state = 'down'
    for mux in muxes:
        proc = subprocess.run(
            ['./peering', 'openvpn', state, mux],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd='./peering_client')


def control_mux_bird(up=True):
    state = 'start'
    if not up:
        state = 'stop'
    proc = subprocess.run(
        ['./peering', 'bgp', state],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd='./peering_client')


def extract_vpn_mux_status():
    mux_status = {}
    proc = subprocess.run(
        ['./peering', 'openvpn', 'status'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd='./peering_client')
    ascii_stdout = proc.stdout.decode('ascii')
    lines = ascii_stdout.splitlines()
    for line in lines:
        mux_match = re.match('^(\S+)\s+(\S+)\s+(\S+)', line)
        if mux_match:
            mux = mux_match.group(1)
            tap = mux_match.group(2)
            status = mux_match.group(3)
            mux_status[mux] = {
                'tap': tap,
                'status': status
            }
    return mux_status


def extract_bird_mux_status():
    mux_status = {}
    proc = subprocess.run(
        ['./peering', 'bgp', 'status'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd='./peering_client')
    ascii_stdout = proc.stdout.decode('ascii')
    lines = ascii_stdout.splitlines()
    for line in lines:
        mux_match = re.match('^(\S+)\s+BGP\s+rtup\s+(\S+)\s+\d+\:\d+\:\d+\s+(\S+)', line)
        if mux_match:
            mux = mux_match.group(1)
            status = mux_match.group(2)
            info = mux_match.group(3)
            mux_status[mux] = {
                'status': status,
                'info': info
            }
    return mux_status


def load_json(filename):
    data = None
    with open(filename, 'r') as f:
        data = json.load(f)
    return data


def dump_json(filename, data, indent=None):
    with open(filename, 'w') as f:
        if indent:
            json.dump(data, f, indent=indent)
        else:
            json.dump(data, f)


def extract_configured_muxes(exp_conf):
    exp_muxes = set()
    for prefix in exp_conf:
        if 'announce' in exp_conf[prefix]:
            for elem in exp_conf[prefix]['announce']:
                if 'muxes' in elem:
                    exp_muxes.update(set(elem['muxes']))
        elif 'withdraw' in exp_conf[prefix]:
            exp_muxes.update(set(exp_conf[prefix]['withdraw']))
    return exp_muxes


def clear_unconfigured_muxes(peer_elements, exp_conf):
    exp_muxes = extract_configured_muxes(exp_conf)
    clean_peer_elements = []
    for elem in peer_elements:
        if elem['BGP Mux'] in exp_muxes:
            clean_peer_elements.append(elem)
    return clean_peer_elements


def extract_keyed_peers(peer_elements, key_field):
    assert key_field in SUPPORTED_PEER_FIELDS
    keyed_peers = {}
    for peer_element in peer_elements:
        key = peer_element[key_field]
        if key not in keyed_peers:
            keyed_peers[key] = []
        keyed_peers[key].append(peer_element)
    return keyed_peers


def map_asn_to_mux_with_rel_info(peer_elements_per_asn):
    asn_to_mux_rel = {}
    mux_to_asn_rel = {}
    for asn in peer_elements_per_asn:
        for peer_element in peer_elements_per_asn[asn]:
            mux = peer_element["BGP Mux"]
            rel = "peer"
            if peer_element["Transit"] == "True":
                rel = "transit"
            if asn not in asn_to_mux_rel:
                asn_to_mux_rel[asn] = {}
            if mux not in mux_to_asn_rel:
                mux_to_asn_rel[mux] = {}
            if mux not in asn_to_mux_rel[asn]:
                asn_to_mux_rel[asn][mux] = set()
            if asn in mux_to_asn_rel[mux]:
                assert rel == mux_to_asn_rel[mux][asn]
            mux_to_asn_rel[mux][asn] = rel
            asn_to_mux_rel[asn][mux].add(rel)
        del_mux = set()
        for mux in asn_to_mux_rel[asn]:
            if len(asn_to_mux_rel[asn][mux]) > 1:
                del_mux.add(mux)
            else:
                asn_to_mux_rel[asn][mux] = list(asn_to_mux_rel[asn][mux])[0]
        for mux in del_mux:
            del asn_to_mux_rel[asn][mux]
        if len(asn_to_mux_rel[asn]) == 0:
            del asn_to_mux_rel[asn]
    return (asn_to_mux_rel, mux_to_asn_rel)


def map_asn_to_u_mux_rel(asn_to_mux_rel, mux_to_asn_rel):
    asn_to_u_mux = {}
    asn_to_u_mux_rel = {}
    mux_to_u_asn = {}
    mux_to_u_asn_rel = {}
    for asn in asn_to_mux_rel:
        mux_to_rel = asn_to_mux_rel[asn]
        # single mux
        if len(mux_to_rel) == 1:
            u_mux = list(mux_to_rel.keys())[0]
            asn_to_u_mux[asn] = u_mux
            asn_to_u_mux_rel[asn] = [u_mux, mux_to_rel[u_mux]]
        else:
            # first map rel to mux(es)
            rel_to_mux = {}
            for mux in mux_to_rel:
                rel = mux_to_rel[mux]
                if rel not in rel_to_mux:
                    rel_to_mux[rel] = set()
                rel_to_mux[rel].add(mux)
            # then check if 'peer' and 'transit' exist --> prefer transit
            if 'transit' in rel_to_mux:
                if len(rel_to_mux['transit']) == 1:
                    u_mux = list(rel_to_mux['transit'])[0]
                    asn_to_u_mux[asn] = u_mux
                    asn_to_u_mux_rel[asn] = [u_mux, 'transit']
            elif 'peer' in rel_to_mux:
                if len(rel_to_mux['peer']) == 1:
                    u_mux = list(rel_to_mux['peer'])[0]
                    asn_to_u_mux[asn] = u_mux
                    asn_to_u_mux_rel[asn] = [u_mux, 'peer']
    all_other_mux_asns = {}
    for mux in mux_to_asn_rel:
        all_other_mux_asns[mux] = set()
        for other_mux in mux_to_asn_rel:
            if mux != other_mux:
                all_other_mux_asns[mux].update(set(mux_to_asn_rel[other_mux].keys()))
    for mux in mux_to_asn_rel:
        if not set(mux_to_asn_rel[mux].keys()).intersection(all_other_mux_asns[mux]):
            u_asns = list(mux_to_asn_rel[mux].keys())
            mux_to_u_asn[mux] = u_asns
            mux_to_u_asn_rel[mux] = {}
            for u_asn in u_asns:
                mux_to_u_asn_rel[mux][u_asn] = mux_to_asn_rel[mux][u_asn]
    return (asn_to_u_mux, asn_to_u_mux_rel, mux_to_u_asn, mux_to_u_asn_rel)


def map_peers_key_to_value(peer_elements, key, value):
    assert key in SUPPORTED_PEER_FIELDS
    assert value in SUPPORTED_PEER_FIELDS
    key_to_value = {}
    for peer_element in peer_elements:
        if peer_element[key] not in key_to_value:
            key_to_value[peer_element[key]] = set([peer_element[value]])
        else:
            key_to_value[peer_element[key]].add(peer_element[value])
    return key_to_value


def key_to_unique_value(key_to_value):
    key_to_u_value = {}
    for key in key_to_value:
        if len(key_to_value[key]) == 1:
            key_to_u_value[key] = list(key_to_value[key])[0]
    return key_to_u_value
