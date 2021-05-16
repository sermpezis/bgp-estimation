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
OUTPUT_FILE_FORMAT = './example_results_impact__CAIDA{}_sims{}_hijackType{}_rnd_monitors_and_RC_and_RA.csv'
NB_RND_MONITORS = [5,10,20,30,40,50,100,200,300,400,500,1000]
RIPE_ATLAS_FILE = '../data/RA_monitors_in_experiments.json'
RIPE_RC_FILE = '../data/RC_monitors_in_experiments.json'




'''
read the input arguments; if incorrect arguments, exit
'''  
if len(sys.argv) is 4:
	nb_of_sims = int(sys.argv[1]) # e.g., 1000
	hijack_type = int(sys.argv[2]) # e.g., 0 or 1 or 2 or ...
	dataset = sys.argv[3] # e.g., 20190801
else:
	sys.exit("Incorrent arguments. Arguments should be {nb_of_sims, hijack_type, dataset_id}")



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
DATA = []
for i in range(nb_of_sims):
	print('simulation step: '+str(100*simulation_step/nb_of_sims)+'%\r',end='')
	simulation_step += 1

	# randomly select victim, hijacker
	r = random.sample(list_of_ASNs,2)
	legitimate_AS = r[0]
	hijacker_AS = r[1]

	# create an IP prefix (here, we arbitrarity set the prefix value equal to the simulation run, i.e., 0, 1, 2, ... . You can use any other value)
	prefix = simulation_step

	# do the legitimate announcement from the victim
	Topo.add_prefix(legitimate_AS,prefix)
	
	simulation_DATA = []	# "simulation_DATA" will contain the data to be saved as the output of the simulation
	simulation_DATA.append(legitimate_AS)	# store the ASN of the legitimate AS
	simulation_DATA.append(hijacker_AS) # store the ASN of the hijacker AS
	simulation_DATA.append(Topo.get_nb_of_nodes_with_path_to_prefix(prefix))	# store the number of ASes that have a path to the prefix
	simulation_DATA.append(Topo.get_nb_of_nodes_with_hijacked_path_to_prefix(prefix,hijacker_AS)) 	# store the number of ASes, whose path to the prefix is through the hijacker (before the hijack takes place)

	# do the hijack from the hijacker
	Topo.do_hijack(hijacker_AS,prefix,hijack_type)
	simulation_DATA.append(Topo.get_nb_of_nodes_with_hijacked_path_to_prefix(prefix,hijacker_AS))

	# impact of the hijack as seen by a set (of size M) of random monitors
	for M in NB_RND_MONITORS:
		simulation_DATA.append(Topo.get_nb_of_nodes_with_hijacked_path_to_prefix(prefix,hijacker_AS,list_of_nodes=random.sample(list_of_ASNs,M)))
	
	# impact of the hijack as seen by a set (of size M) of RC monitors
	for M in NB_RND_MONITORS:
		if M < len(Route_collectors):
			simulation_DATA.append(Topo.get_nb_of_nodes_with_hijacked_path_to_prefix(prefix,hijacker_AS,list_of_nodes=random.sample(Route_collectors,M)))
		else:
			simulation_DATA.append(-1)

	# impact of the hijack as seen by a set (of size M) of RA monitors
	for M in NB_RND_MONITORS:
		if M < len(Ripe_atlas):
			simulation_DATA.append(Topo.get_nb_of_nodes_with_hijacked_path_to_prefix(prefix,hijacker_AS,list_of_nodes=random.sample(Ripe_atlas,M)))
		else:
			simulation_DATA.append(-1)

	DATA.append(simulation_DATA)

	# withdraws all IP prefixes from the topology - clears the routing tables of all ASes (this is optional; used for memory performance reasons) 
	Topo.clear_routing_information()




'''
Write the results to a csv file
'''
print('Writing statistics to csv...')
csvfilename = OUTPUT_FILE_FORMAT.format(dataset, nb_of_sims, hijack_type)
with open(csvfilename, 'w') as csvfile:
	writer = csv.writer(csvfile, delimiter=',')
	writer.writerows(DATA)
