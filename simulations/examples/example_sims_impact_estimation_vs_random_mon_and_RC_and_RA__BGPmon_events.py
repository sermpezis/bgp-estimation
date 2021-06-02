#!/usr/bin/env python3
#
#
# Author: Pavlos Sermpezis
# Institute of Computer Science, Foundation for Research and Technology - Hellas (FORTH), Greece
#
# E-mail: sermpezis@ics.forth.gr
#
#


#import time
import random
import csv
import sys
sys.path.insert(1, './BGP_simulator/')
from BGPtopology import BGPtopology
import util_functions as utils

TOPOLOGY_FILE_FORMAT = '../CAIDA AS-graph/{}.as-rel2.txt'
OUTPUT_FILE_FORMAT = './example_results_impact__CAIDA{}_sims{}_hijackType{}_rnd_monitors_and_RC_and_RA__BGPmon_events.csv'
NB_RND_MONITORS = [5,10,20,30,40,50,100,200,300,400,500,1000]
RIPE_ATLAS_FILE = '../data/RA_monitors_in_experiments.json'
RIPE_RC_FILE = '../data/RC_monitors_in_experiments.json'
BGPmon_file = '../data/BGPmon_possible_hijacks_exported.csv'



'''
read the input arguments; if incorrect arguments, exit
'''  
if len(sys.argv) is 3:
	hijack_type = int(sys.argv[1]) # 0 or 1 or 2 or ...
	dataset = sys.argv[2] # 20160901
else:
	sys.exit("Incorrent arguments. Arguments should be {hijack_type, dataset_id}")



'''
load and create topology
'''
print('Loading topology...')
Topo = BGPtopology()
Topo.load_topology_from_csv(TOPOLOGY_FILE_FORMAT.format(dataset))
list_of_ASNs = Topo.get_all_nodes_ASNs()

'''
add to the topology the list of RIPE (RIS & Atlas) monitors (i.e., ASNs of the members of the RIPE RIS route collectors / RIPE Atlas probes)
'''
Ripe_atlas = list(set(list_of_ASNs).intersection(set(utils.get_list_monitor_ASes(RIPE_ATLAS_FILE))))
Route_collectors = list(set(list_of_ASNs).intersection(set(utils.get_list_monitor_ASes(RIPE_RC_FILE))))


'''
do simulations:
	for each run, 
	(i) select randomly a legitimate and a hijacking AS
	(ii) add a new prefix to the legitimate AS (BGP messages for the prefix will start propagating)
	(iii) hijack the prefix from the hijacker AS
'''

print('Simulation started')
simulation_step = 0
simulation_step_valid = 0
DATA = []
with open(BGPmon_file, 'r') as f:
	cr = csv.reader(f,delimiter=',')
	for r in cr:
		print('simulation step (only valid & all): {} ({}) \r'.format(simulation_step_valid, simulation_step),end='')
		simulation_step += 1
		
		legitimate_AS = int(r[1])
		hijacker_AS = int(r[0])

		if (legitimate_AS in list_of_ASNs) and (hijacker_AS in list_of_ASNs):
			simulation_step_valid += 1

			prefix = simulation_step

			# do the legitimate announcement from the victim
			Topo.add_prefix(legitimate_AS,prefix)
			
			simulation_DATA = []	# "simulation_DATA" will contain the data to be saved as the output of the simulation
			simulation_DATA.append(legitimate_AS)
			simulation_DATA.append(hijacker_AS)
			simulation_DATA.append(Topo.get_nb_of_nodes_with_path_to_prefix(prefix))
			simulation_DATA.append(Topo.get_nb_of_nodes_with_hijacked_path_to_prefix(prefix,hijacker_AS))

			# do the hijack from the hijacker
			Topo.do_hijack(hijacker_AS,prefix,hijack_type)
			simulation_DATA.append(Topo.get_nb_of_nodes_with_hijacked_path_to_prefix(prefix,hijacker_AS))

			# impact of the hijack as seen by random monitors
			for M in NB_RND_MONITORS:
				simulation_DATA.append(Topo.get_nb_of_nodes_with_hijacked_path_to_prefix(prefix,hijacker_AS,list_of_nodes=random.sample(list_of_ASNs,M)))
			
			# impact of the hijack as seen by RC monitors
			for M in NB_RND_MONITORS:
				if M < len(Route_collectors):
					simulation_DATA.append(Topo.get_nb_of_nodes_with_hijacked_path_to_prefix(prefix,hijacker_AS,list_of_nodes=random.sample(Route_collectors,M)))
				else:
					simulation_DATA.append(-1)

			# impact of the hijack as seen by RA monitors
			for M in NB_RND_MONITORS:
				if M < len(Ripe_atlas):
					simulation_DATA.append(Topo.get_nb_of_nodes_with_hijacked_path_to_prefix(prefix,hijacker_AS,list_of_nodes=random.sample(Ripe_atlas,M)))
				else:
					simulation_DATA.append(-1)

			DATA.append(simulation_DATA)
			Topo.clear_routing_information()




'''
Write the results to a csv file
'''
print('Writing statistics to csv...')
csvfilename = OUTPUT_FILE_FORMAT.format(dataset, simulation_step_valid, hijack_type)
with open(csvfilename, 'w') as csvfile:
	writer = csv.writer(csvfile, delimiter=',')
	writer.writerows(DATA)
