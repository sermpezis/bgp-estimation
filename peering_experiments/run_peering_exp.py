#!/usr/bin/env python3


import argparse
import subprocess
import sys
import os
import time
import utils
sys.path.insert(0, './peering_client')
from datetime import datetime
from peering import AnnouncementController as ACtrl

# set global vars
WAIT_CONVERGE = 60*20 # wait 20 minutes for BGP to converge
WAIT_BGPSTREAM = 60*30 # wait another 30 minutes for BGPStream updates to be available
WAIT_TRACE = 60*30 # wait 30 minutes for traceroutes to complete before analyzing them
SAFE_INTERVAL = 60 # wait 1 minute between consecutive PEERING actions
PY_BIN = '/usr/bin/python2'
PY3_BIN = '/usr/bin/python3'
TRACE_ISSUE_PY = 'issue_traceroutes_to_prefix.py'
TRACE_TRANS_PY = 'translate_traceroutes_to_catchment.py'
DP_PROBE_ISSUE_PY = 'issue_pings_to_asns.py'
DP_PROBE_TRANS_PY = 'translate_dp_probes_to_catchment.py'
BGPSTREAM_GET_PY = 'upd_get_bgpstream_paths_for_prefix.py'
BGPSTREAM_TRANS_PY = 'translate_bgpstream_paths_to_catchment.py'
FINAL_INFO_PY = 'parse_final_exp_info.py'

# parse input arguments
parser = argparse.ArgumentParser(description="run PEERING MOAS experiment")
parser.add_argument('-e', '--experiment', dest='experiment_json', type=str,
                    help='json file with PEERING experiment specification', required=True)
parser.add_argument('-p', '--peering_peers', dest='peering_peers_json', type=str,
                    help='json file with PEERING peers', default='./peers.json')
parser.add_argument('-i', '--ip_to_as', dest='ip_to_as', type=str,
                    help='ip (pfx) to AS db json', default="../pfx2as/data/dbs/2019_10_db.json")
parser.add_argument('-t', '--traceroutes', dest='run_traceroutes', action='store_true',
                     help='flag to indicate if traceroutes should run')
parser.add_argument('-d', "--dp_probing", dest="dp_probing", action='store_true',
                    help="flag to indicate if data-plane probing (pings) will be used")
parser.add_argument('-b', "--bgpstream", dest="bgpstream", action='store_true',
                    help="flag to indicate if bgpstream data collection will be used")
parser.add_argument('-a', '--analyze', dest='analyze', action='store_true',
                    help='flag to indicate if results (pings, traceroutes, BGP paths) should be analyzed')
parser.add_argument('-x', "--existing_exp_dir", dest="existing_exp_dir", type=str,
                    help="existing experiment location (only if not new experiment in BGP", default="")
args = parser.parse_args()

if args.existing_exp_dir == "":
    # create needed experiment folders
    print("Preparing control-plane experiment...")
    utils.create_dir('experiments')
    date = datetime.utcnow()
    assert os.path.isfile(args.experiment_json)
    assert os.path.isfile(args.peering_peers_json)
    assert os.path.isfile(args.ip_to_as)
    exp_name = args.experiment_json.split('/')[-1].split('.json')[0]
    exp_dir = 'experiments/{}_Y{}_M{}_D{}_H{}_M{}'.format(
        exp_name,
        date.year,
        date.month,
        date.day,
        date.hour,
        date.minute
    )
    utils.create_dir(exp_dir)
    control_plane_dir = '{}/{}'.format(exp_dir, 'control_plane')
    utils.create_dir(control_plane_dir)
    if args.run_traceroutes or args.dp_probing:
        data_plane_dir = '{}/{}'.format(exp_dir, 'data_plane')
        utils.create_dir(data_plane_dir)
    assert os.path.isfile(args.peering_peers_json)
    assert os.path.isfile(args.ip_to_as)

    # load experiment data
    print('\tLoading control-plane experiment data...')
    exp_conf = utils.load_json(args.experiment_json)
    conf_prefix = list(exp_conf.keys())[0]
    subprocess.run(['cp', args.experiment_json, control_plane_dir])
    exp_muxes = utils.extract_configured_muxes(exp_conf)
    utils.dump_json('{}/exp_configured_muxes.json'.format(control_plane_dir), list(exp_muxes))
    subprocess.run(['cp', args.peering_peers_json, control_plane_dir])
    peer_elements = utils.load_json(args.peering_peers_json)
    peer_elements = utils.clear_unconfigured_muxes(peer_elements, exp_conf)
    peer_elements_per_asn = utils.extract_keyed_peers(peer_elements, "Peer ASN")
    (asn_to_mux_rel, mux_to_asn_rel) = utils.map_asn_to_mux_with_rel_info(peer_elements_per_asn)
    (asn_to_u_mux, asn_to_u_mux_rel, mux_to_u_asn, mux_to_u_asn_rel) = utils.map_asn_to_u_mux_rel(asn_to_mux_rel, mux_to_asn_rel)
    utils.dump_json('{}/asn_to_u_mux.json'.format(control_plane_dir), asn_to_u_mux)
    utils.dump_json('{}/asn_to_u_mux_rel.json'.format(control_plane_dir), asn_to_u_mux_rel)
    utils.dump_json('{}/mux_to_u_asn.json'.format(control_plane_dir), mux_to_u_asn)
    utils.dump_json('{}/mux_to_u_asn_rel.json'.format(control_plane_dir), mux_to_u_asn_rel)
    (mux_to_origin, origin_to_mux) = utils.map_origin_asn_to_mux(args.experiment_json)
    utils.dump_json('{}/mux_to_origin.json'.format(control_plane_dir), mux_to_origin)
    utils.dump_json('{}/origin_to_mux.json'.format(control_plane_dir), origin_to_mux)

    # load initial mux names and VPN statuses
    print('\tRetrieving initial muxes and VPN statuses...')
    init_vpn_mux_status = utils.extract_vpn_mux_status()
    available_peering_muxes = set(init_vpn_mux_status.keys())
    utils.dump_json('{}/available_muxes.json'.format(control_plane_dir), list(available_peering_muxes))
    if len(exp_muxes - available_peering_muxes) != 0:
        print('The experiment cannot be conducted since not all configured muxes are available!')
        print('Non-available muxes: {}'.format(exp_muxes - available_peering_muxes))
        print('Exiting...')
        sys.exit(1)

    # bring up required VPN mux tunnels
    print('\tBringing up required VPN tunnels...')
    utils.control_mux_tun(exp_muxes, up=True)
    time.sleep(SAFE_INTERVAL)
    vpn_mux_status = utils.extract_vpn_mux_status()
    utils.dump_json('{}/vpn_mux_status.json'.format(control_plane_dir), vpn_mux_status)
    live_peering_muxes = set([mux for mux in vpn_mux_status if vpn_mux_status[mux]['status'] == 'up'])
    if len(exp_muxes - live_peering_muxes) != 0:
        print('The experiment cannot be conducted since not all configured muxes (VPN) are up!')
        print('Down muxes: {}'.format(exp_muxes - live_peering_muxes))
        print("Cleaning up...")
        utils.cleanup_exp_state(available_peering_muxes)
        print('Exiting...')
        sys.exit(1)

    # bring up bird sessions on the muxes
    print('\tBringing up required BIRD BGP sessions...')
    time.sleep(SAFE_INTERVAL)
    utils.control_mux_bird(up=True)
    time.sleep(SAFE_INTERVAL)
    bird_mux_status = utils.extract_bird_mux_status()
    utils.dump_json('{}/bird_mux_status.json'.format(control_plane_dir), bird_mux_status)
    live_peering_muxes = set([mux for mux in bird_mux_status if bird_mux_status[mux]['status'] == 'up' and
                              bird_mux_status[mux]['info'] == 'Established'])
    if len(exp_muxes - live_peering_muxes) != 0:
        print('The experiment cannot be conducted since not all configured muxes (Bird) are up!')
        print('Down muxes: {}'.format(exp_muxes - live_peering_muxes))
        print("Cleaning up...")
        utils.cleanup_exp_state(available_peering_muxes)
        print('Exiting...')
        sys.exit(1)
    utils.dump_json('{}/live_muxes.json'.format(control_plane_dir), list(live_peering_muxes))

    # configure experiment controller
    print('\tConfiguring control-plane experiment controller...')
    time.sleep(SAFE_INTERVAL)
    bird_cfg_dir = 'peering_client/configs/bird'
    bird_sock = 'peering_client/var/bird.ctl'
    schema_fn = 'peering_client/configs/announcement_schema.json'
    exp_ctrl = ACtrl(bird_cfg_dir, bird_sock, schema_fn)

    # run control-plane PEERING experiment
    print("Running control-plane experiment for prefix '{}'...".format(conf_prefix))
    exp_ctrl.deploy(exp_conf)
    time_now = int(time.time())
    cp_metadata = {
        'timestamp': time_now,
        'start_check': time_now - 5*60,
        'end_check': time_now + 20*60
    }
    utils.dump_json('{}/metadata.json'.format(control_plane_dir), cp_metadata)

    # wait for BGP convergence
    print("Waiting {}s for BGP to converge...".format(WAIT_CONVERGE))
    time.sleep(WAIT_CONVERGE)

    if exp_name.startswith('withdraw'):
        print("Cleaning up...")
        time.sleep(SAFE_INTERVAL)
        utils.cleanup_exp_state(available_peering_muxes)
        sys.exit(1)
else:
    exp_dir = args.existing_exp_dir.rstrip('/')
    exp_conf = utils.load_json(args.experiment_json)
    conf_prefix = list(exp_conf.keys())[0]
    data_plane_dir = '{}/{}'.format(exp_dir, 'data_plane')
    control_plane_dir = '{}/{}'.format(exp_dir, 'control_plane')
    cp_metadata = utils.load_json('{}/metadata.json'.format(control_plane_dir))

# initiate traceroute probing
if args.run_traceroutes:
    print("Issuing traceroutes to prefix '{}'...".format(conf_prefix))
    cmd_list = [PY3_BIN, TRACE_ISSUE_PY,
                '-t', conf_prefix,
                '-d', data_plane_dir]
    cmd_str = ' '.join(cmd_list)
    print('\tRunning: {}'.format(cmd_str))
    subprocess.run(cmd_list)
    print("\tWaiting {}s for traceroutes to complete...".format(WAIT_TRACE))
    time.sleep(WAIT_TRACE)

    # analyze traceroute results (to-catchment translation)
    if args.analyze:
        print("\tAnalyzing traceroutes...")
        cmd_list = [PY3_BIN, TRACE_TRANS_PY,
                    '-i', args.ip_to_as,
                    '-d', data_plane_dir,
                    '-c', control_plane_dir]
        cmd_str = ' '.join(cmd_list)
        print('\tRunning: {}'.format(cmd_str))
        subprocess.run(cmd_list)

# initiate BGPStream path collection
if args.bgpstream:
    # no need to double-wait
    if not args.run_traceroutes:
        print("Waiting {}s for BGPStream to become available...".format(WAIT_BGPSTREAM))
        time.sleep(WAIT_BGPSTREAM)
    print('\tRetrieving bgpstream paths...')
    cmd_list = [PY_BIN, BGPSTREAM_GET_PY,
                '-p', conf_prefix,
                '-s', str(cp_metadata['start_check']),
                '-e', str(cp_metadata['end_check']),
                '-c', control_plane_dir]
    cmd_str = ' '.join(cmd_list)
    print('\tRunning: {}'.format(cmd_str))
    subprocess.run(cmd_list)

    # analyze BGPStream path results (to-catchment translation)
    if args.analyze:
        print('\tAnalyzing bgpstream paths...')
        bgpstream_file = '{}/bgpstream_paths_for_prefix_{}_{}_{}_{}.csv'.format(
            control_plane_dir,
            conf_prefix[0:-3],
            conf_prefix[-2:],
            cp_metadata['start_check'],
            cp_metadata['end_check'])
        cmd_list = [PY3_BIN, BGPSTREAM_TRANS_PY,
                    '-b', bgpstream_file,
                    '-c', control_plane_dir]
        cmd_str = ' '.join(cmd_list)
        print('\tRunning: {}'.format(cmd_str))
        subprocess.run(cmd_list)

# initiate data plane probing (pings)
if args.dp_probing:
    print("Issuing data plane probes to all ASNs...")
    cmd_list = [
        PY3_BIN,
        DP_PROBE_ISSUE_PY,
        "--ip_to_as",
        args.ip_to_as,
        "--cp_dir",
        control_plane_dir,
        "--dp_dir",
        data_plane_dir
    ]
    cmd_str = ' '.join(cmd_list)
    print('\tRunning: {}'.format(cmd_str))
    subprocess.run(cmd_list)

    # analyze data plane probing results (to-catchment translation)
    if args.analyze:
        print("\tAnalyzing data plane probes...")
        cmd_list = [
            PY3_BIN,
            DP_PROBE_TRANS_PY,
            '-c',
            control_plane_dir,
            '-d',
            data_plane_dir
        ]
        cmd_str = ' '.join(cmd_list)
        print('\tRunning: {}'.format(cmd_str))
        subprocess.run(cmd_list)

# # produce final experiment information
# if args.analyze:
#     print("\tGenerating final exp info...")
#     cmd_list = [
#         PY3_BIN,
#         FINAL_INFO_PY,
#         '-e',
#         exp_dir
#     ]
#     cmd_str = ' '.join(cmd_list)
#     print('\tRunning: {}'.format(cmd_str))
#     subprocess.run(cmd_list)
