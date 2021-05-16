#!/usr/bin/env python3
#
#
# Author: Pavlos Sermpezis
# Institute of Computer Science, Foundation for Research and Technology - Hellas (FORTH), Greece
#
# E-mail: sermpezis@ics.forth.gr
#
#
# This file is part of the BGPsimulator
#

import csv
import json
from BGPnode import BGPnode
from IXPNode import IXPNode

class BGPtopology:
	''' 
	Class for network topology, where ASes are represented as single nodes (BGPnodes). 
	A BGPtopology contais a list of the member nodes (objects of type BGPnode).
	In this class, there exist methods related to (a) adding member nodes and links, (b) adding and hijacking IPprefixes, (c) obtaining various information from the member nodes of the topology.

	class variables: 
		(a) list_of_all_BGP_nodes:	dictionary (initially empty) - dictionary with (i) keys the ASNs of member nodes and (ii) values the objects of type BGPnode (corresponding to each member node)
	'''


	'''
	Contructor for object of the class BGPtopology. Creates the class variable "list_of_all_BGP_nodes" as an empty dictionary.
	'''
	def __init__(self):
		self.list_of_all_BGP_nodes = {}

	
	'''
	Adds a node to the topology, i.e., to the dictionary "list_of_all_BGP_nodes".
	
	IF the given node does not exist in the "list_of_all_BGP_nodes" dictionary, 
	THEN add the node

	Input argument:
		(a) ASN: the ASN of the node to be added
	'''
	def add_node(self,ASN):
		if not self.has_node(ASN):
			self.list_of_all_BGP_nodes[ASN] = BGPnode(ASN,self)

	
	'''
	Remove node from topology.
	Not in use !!!

	TODO: need to implement BGP path withdrawals at the BGPPnode class first, and a destructor, and then can only define this method
	'''
	def remove_node(self,ASN):
		pass
		#if self.has_node(ASN):
		#	del self.list_of_all_BGP_nodes[ASN]


	'''
	Return a node (i.e. the BGPnode object) belonging to the topology.
	
	IF the given node exists in the "list_of_all_BGP_nodes" dictionary, 
	THEN return the node
	
	Input argument:
		(a) ASN: the ASN of the node to be returned

	Returns:
		A BGPnode object corresponding to the given ASN
	'''
	def get_node(self,ASN):
		if self.has_node(ASN):
			return self.list_of_all_BGP_nodes[ASN]

	
	'''
	Checks if the given node exists in the "list_of_all_BGP_nodes" dictionary.
	
	Input argument:
		(a) ASN: the ASN of the node to be checked

	Returns:
		TRUE if it exists, FALSE otherwise
	'''
	def has_node(self,ASN):
		if ASN in self.list_of_all_BGP_nodes.keys():
			return True
		else:
			return False


	
	'''
	Adds a link in the topology between the two given nodes, and annotates the link according to the given peering type.

	IF the given nodes do not exist in the "list_of_all_BGP_nodes" dictionary, 
	THEN 	add them.
	IF a link between the two given nodes does not exist,
	THEN 	add ASN1 to ASN2's neighbors and ASN2 to ASN1's neighbors, and set the peering types according to the given type.
	
	Input arguments:
		(a) ASN1: the AS number of the first node
		(b) ASN2: the AS number of the second node
		(c) peering_type: an int (-1 or 0) that denotes the peering relation type between the two nodes; IF -1 then ASN2 is customer of ASN1, ELSE IF 0 then the nodes are peers
	'''
	def add_link(self,ASN1, ASN2,peering_type):
		if not self.has_node(ASN1):
			self.add_node(ASN1)
		if not self.has_node(ASN2):
			self.add_node(ASN2)
		if not self.has_link(ASN1,ASN2):
			if peering_type == -1:
				self.list_of_all_BGP_nodes[ASN1].add_ASneighbor(ASN2,'customer')
				self.list_of_all_BGP_nodes[ASN2].add_ASneighbor(ASN1,'provider')
			elif peering_type == 0:
				self.list_of_all_BGP_nodes[ASN1].add_ASneighbor(ASN2,'peer')
				self.list_of_all_BGP_nodes[ASN2].add_ASneighbor(ASN1,'peer')
			else:
				print('ERROR: Not valid peering relation')
		else:
			print('ERROR: a link already exists')


	def remove_link(self,ASN1, ASN2):
		if self.has_node(ASN1) and self.has_node(ASN2) and self.has_link(ASN1,ASN2):
			self.list_of_all_BGP_nodes[ASN1].remove_ASneighbor(ASN2)
			self.list_of_all_BGP_nodes[ASN2].remove_ASneighbor(ASN1)


	'''
	Checks if the given link exists in the topology.

	IF both nodes exist in the topology
	THEN 	IF node ASN1 has node ASN2 as neighbor AND node ASN2 has node ASN1 as neighbor
			THEN return TRUE

	
	Input arguments:
		(a) ASN1: the AS number of the first node
		(b) ASN2: the AS number of the second node

	Returns:
		TRUE if the link exists, FALSE otherwise
	'''
	def has_link(self,ASN1,ASN2):
		if self.has_node(ASN1) and self.has_node(ASN2):
			if self.get_node(ASN1).has_ASneighbor(ASN2) or self.get_node(ASN2).has_ASneighbor(ASN1):
				return True
		return False


	'''
	Adds the given prefix to the given node.
	
	IF the node exists in the topology, 
	THEN add the prefix

	Input arguments:
		(a) ASN: the AS number of the node
		(b) IPprefix: the (owned) prefix to be added
	'''
	def add_prefix(self,ASN,IPprefix,forbidden_neighbors=None):
		if self.has_node(ASN):
			self.get_node(ASN).add_prefix(IPprefix,forbidden_neighbors=forbidden_neighbors)


	'''
	Hijack the given prefix from the given node with the given hijack type.
	
	IF the node exists in the topology, 
	THEN hijack the prefix

	Input arguments:
		(a) ASN: the AS number of the node
		(b) IPprefix: the (owned) prefix to be added
		(c) hijack_type: the type of the hijack attack
	'''
	def do_hijack(self,ASN,IPprefix,hijack_type):
		if self.has_node(ASN):
			self.get_node(ASN).do_hijack(IPprefix,hijack_type)



	'''
	Creates the nodes and links of the topology, based on the data of the given csv file.

	(Currently) it supports only files of the "CAIDA AS-relationship dataset" format (http://www.caida.org/data/active/as-relationships/)
	The format is:		ASN1|ASN2|peering_type|other_not_used_fields
				e.g., 	1|11537|0|bgp

	Input arguments:
		(a) file: a string with the name of the csv file to be read
		(b) type: a string denoting the format type of the csv file; default is 'CAIDA' (which is currently the only supported type)
	'''
	def load_topology_from_csv(self,file,type='CAIDA', asn_as_str=False):
		try:
			if type == 'CAIDA':
				with open(file, 'r') as csvfile:
					csvreader = csv.reader(csvfile,delimiter='|')
					for row in csvreader:
						if row[0][0] is not '#':	# ignore lines starting with "#"
							if asn_as_str:
								self.add_link(row[0],row[1],int(row[2]))
							else:
								self.add_link(int(row[0]),int(row[1]),int(row[2]))
		except IOError:
			print('ERROR: file not found')






	### methods to obtain (or print) various information from the member nodes of the topology ###
	# these methods could be used after an experiment, e.g., to  extract statistics for the number of hijacked paths, nodes, etc.



	'''
	Print some information for each node in the topology; see the respective method defined in the BGPnode class
	'''
	def print_info(self):
		for key,node in self.list_of_all_BGP_nodes.items():
			node.print_info()

	'''
	Returns the number of nodes in the topology, i.e., the length (number of keys) of the dictionary "list_of_all_BGP_nodes"
	'''
	def get_nb_nodes(self):
		return len(self.list_of_all_BGP_nodes)

	'''
	Returns a list containing the ASNs (integers) of the nodes in the topology
	'''
	def get_all_nodes_ASNs(self):
		return list(self.list_of_all_BGP_nodes.keys())


	'''
	Returns a list containing the IP prefixes of all the nodes in the topology
	'''
	def get_list_of_prefixes(self):
		list_of_prefixes = {}
		for key,node in self.list_of_all_BGP_nodes.items():
			if node.get_prefixes():
				list_of_prefixes[key] = list(node.get_prefixes())
		return list_of_prefixes


	'''
	Returns a list containing the hijacked IP prefixes of all the nodes in the topology
	'''
	def get_list_of_hijacked_prefixes(self):
		list_of_hijacked_prefixes = {}
		for key,node in self.list_of_all_BGP_nodes.items():
			if node.get_hijacked_prefixes():
				list_of_hijacked_prefixes[key] = list(node.get_hijacked_prefixes().keys())
		return list_of_hijacked_prefixes

	
	'''
	Returns a dictionary containing (a) as keys the hijacked IP prefixes of all the nodes in the topology and (b) as values the node that hijacked the prefix. 
	'''
	def get_list_of_hijacked_prefixes_and_hijackers(self):
		hijacked_prefixes_and_hijackers = {}
		for key,node in self.list_of_all_BGP_nodes.items():
			if node.get_hijacked_prefixes():
				for prefix in list(node.get_hijacked_prefixes().keys()):
					hijacked_prefixes_and_hijackers[prefix] = node.ASN
		return hijacked_prefixes_and_hijackers



	'''
	Returns the number of the (given) nodes that have a path to the given prefix (and, if any ASN is given, consider only paths originated by the given ASN)

	IF a list_of_nodes is given:
	THEN 	consider only the list of the given nodes (that exist in the topology)
	ELSE 	consider every node in the topology

	FOR all the considered nodes
		IF the node has a path to the prefix
		THEN	IF an ASN is given
				THEN 	IF the path that the node has, is originated by the given ASN, 
						THEN increment the nb_of_nodes_with_path_to_prefix
				ELSE 	increment the nb_of_nodes_with_path_to_prefix

	Input arguments:
		(a) IPprefix: 		the prefix for which paths to be considered
		(b) origin_ASN: 	the origin ASN for the paths (i.e., the first ASN in the path) to be considered; defount value is None (i.e., consider paths from any origin AS)
		(c) list_of_nodes: 	the list of nodes, which will be considered ; default value is None (i.e., consider all the nodes of the topology)

	Returns:
		An integer denoting the number of nodes 
	'''
	def get_nb_of_nodes_with_path_to_prefix(self,IPprefix,origin_ASN = None, list_of_nodes=None):
		nb_of_nodes_with_path_to_prefix = 0

		if list_of_nodes:
			list_of_nodes_to_search = {}
			for key in list_of_nodes:
				if key in self.list_of_all_BGP_nodes.keys():
					list_of_nodes_to_search[key] = self.list_of_all_BGP_nodes[key]
		else:
			list_of_nodes_to_search = self.list_of_all_BGP_nodes

		for key,node in list_of_nodes_to_search.items():
			if node.paths.get(IPprefix):
				if origin_ASN:
					if node.paths.get(IPprefix)[-1] == origin_ASN:	# in case there is path, check the origin AS in the path
						nb_of_nodes_with_path_to_prefix += 1
				else:
					nb_of_nodes_with_path_to_prefix += 1

		return nb_of_nodes_with_path_to_prefix



	'''
	Returns the number of the (given) nodes that have a path (for the given prefix) that includes the hijacker ASN.

	IF a list_of_nodes is given:
	THEN 	consider only the list of the given nodes (that exist in the topology)
	ELSE 	consider every node in the topology

	FOR all the considered nodes
		IF the node has a path to the prefix
		THEN	IF the path contains the given ASN
				THEN 	increment the nb_of_nodes_with_path_to_prefix

	Input arguments:
		(a) IPprefix: 		the prefix for which paths to be considered
		(b) origin_ASN: 	the origin ASN for the paths (i.e., the first ASN in the path) to be considered; defount value is None (i.e., consider paths from any origin AS)
		(c) list_of_nodes: 	the list of nodes, which will be considered ; default value is None (i.e., consider all the nodes of the topology)

	Returns:
		An integer denoting the number of nodes 
	'''
	def get_nb_of_nodes_with_hijacked_path_to_prefix(self,IPprefix,hijacker_ASN, list_of_nodes=None):
		nb_of_nodes_with_path_to_prefix = 0

		if list_of_nodes:
			list_of_nodes_to_search = {}
			for key in list_of_nodes:
				if key in self.list_of_all_BGP_nodes.keys():
					list_of_nodes_to_search[key] = self.list_of_all_BGP_nodes[key]
		else:
			list_of_nodes_to_search = self.list_of_all_BGP_nodes

		for key,node in list_of_nodes_to_search.items():
			if node.paths.get(IPprefix):
				if hijacker_ASN in node.paths.get(IPprefix):
					nb_of_nodes_with_path_to_prefix += 1

		return nb_of_nodes_with_path_to_prefix


	'''
	Returns the average path length that (the given) nodes have for the given prefix.

	IF a list_of_nodes is given:
	THEN 	consider only the list of the given nodes (that exist in the topology)
	ELSE 	consider every node in the topology

	FOR all the considered nodes
		IF the node has a path to the prefix
		THEN	IF the path contains the given ASN
				THEN 	increment the nb_of_nodes_with_path_to_prefix

	Input arguments:
		(a) IPprefix: 		the prefix for which paths to be considered
		(b) list_of_nodes: 	the list of nodes, which will be considered ; default value is None (i.e., consider all the nodes of the topology)

	Returns:
		An number denoting the average path length (i.e., sum of path length over the number of nodes with path to prefix)
	'''
	def get_average_path_length(self,IPprefix,list_of_nodes=None):
		nb_of_nodes_with_path_to_prefix = 0
		sum_path_lengths = 0

		if list_of_nodes:
			list_of_nodes_to_search = {}
			for key in list_of_nodes:
				if key in self.list_of_all_BGP_nodes.keys():
					list_of_nodes_to_search[key] = self.list_of_all_BGP_nodes[key]
		else:
			list_of_nodes_to_search = self.list_of_all_BGP_nodes

		for key,node in list_of_nodes_to_search.items():
			if node.paths.get(IPprefix):
				sum_path_lengths = sum_path_lengths + len(node.paths.get(IPprefix))
				nb_of_nodes_with_path_to_prefix += 1

		if nb_of_nodes_with_path_to_prefix == 0:
			average_path_length = 0
		else:
			average_path_length = sum_path_lengths/nb_of_nodes_with_path_to_prefix

		return average_path_length



		'''
	Returns the set of the (given) nodes that have a path to the given prefix (and, if any ASN is given, consider only paths originated by the given ASN)

	IF a list_of_nodes is given:
	THEN 	consider only the list of the given nodes (that exist in the topology)
	ELSE 	consider every node in the topology

	FOR all the considered nodes
		IF the node has a path to the prefix
		THEN	IF an ASN is given
				THEN 	IF the path that the node has, is originated by the given ASN,
						THEN increment the nb_of_nodes_with_path_to_prefix
				ELSE 	add node to the set_of_nodes_with_path_to_prefix

	Input arguments:
		(a) IPprefix: 		the prefix for which paths to be considered
		(b) origin_ASN: 	the origin ASN for the paths (i.e., the first ASN in the path) to be considered; defount value is None (i.e., consider paths from any origin AS)
		(c) list_of_nodes: 	the list of nodes, which will be considered ; default value is None (i.e., consider all the nodes of the topology)

	Returns:
		A set of ASNs
	'''
	def get_set_of_nodes_with_path_to_prefix(self,IPprefix,origin_ASN = None, list_of_nodes=None):
		set_of_nodes_with_path_to_prefix = set()

		if list_of_nodes:
			list_of_nodes_to_search = {}
			for key in list_of_nodes:
				if key in self.list_of_all_BGP_nodes.keys():
					list_of_nodes_to_search[key] = self.list_of_all_BGP_nodes[key]
		else:
			list_of_nodes_to_search = self.list_of_all_BGP_nodes

		for key,node in list_of_nodes_to_search.items():
			if node.paths.get(IPprefix):
				if origin_ASN:
					if node.paths.get(IPprefix)[-1] == origin_ASN:	# in case there is path, check the origin AS in the path
						set_of_nodes_with_path_to_prefix.add(node.ASN)
				else:
					set_of_nodes_with_path_to_prefix.add(node.ASN)

		return set_of_nodes_with_path_to_prefix

	'''
	Returns the set of the (given) nodes that have a path (for the given prefix) that includes the hijacker ASN.

	IF a list_of_nodes is given:
	THEN 	consider only the list of the given nodes (that exist in the topology)
	ELSE 	consider every node in the topology

	FOR all the considered nodes
		IF the node has a path to the prefix
		THEN	IF the path contains the given ASN
				THEN 	add node to the set_of_nodes_with_path_to_prefix

	Input arguments:
		(a) IPprefix: 		the prefix for which paths to be considered
		(b) hijacker_ASN: 	the hijacker ASN for the paths to be considered
		(c) list_of_nodes: 	the list of nodes, which will be considered ; default value is None (i.e., consider all the nodes of the topology)

	Returns:
		A set of ASNs
	'''
	def get_set_of_nodes_with_hijacked_path_to_prefix(self,IPprefix,hijacker_ASN, list_of_nodes=None):
		set_of_nodes_with_path_to_prefix = set()

		if list_of_nodes:
			list_of_nodes_to_search = {}
			for key in list_of_nodes:
				if key in self.list_of_all_BGP_nodes.keys():
					list_of_nodes_to_search[key] = self.list_of_all_BGP_nodes[key]
		else:
			list_of_nodes_to_search = self.list_of_all_BGP_nodes

		for key,node in list_of_nodes_to_search.items():
			if node.paths.get(IPprefix):
				if hijacker_ASN in node.paths.get(IPprefix):
					set_of_nodes_with_path_to_prefix.add(node.ASN)

		return set_of_nodes_with_path_to_prefix

	

	'''
	Returns the set of the nodes seen in the AS paths of the (given) monitors that have a path (for the given prefix) that includes the hijacker ASN.

	Finds the ASes in the given list_of_monitors that are nodes of the topology

	FOR all the considered monitors
		IF the monitor has a path to the prefix AND the path contains the given ASN
			THEN 	add the monitor and all nodes appearing in the path before the hijacker, to the set_of_seen_infected_nodes

	Input arguments:
		(a) IPprefix: 		the prefix for which paths to be considered
		(b) hijacker_ASN: 	the hijacker ASN for the paths to be considered
		(c) list_of_monitors: 	the list of monitors, which will be considered

	Returns:
		A set of ASNs
	'''
	def get_set_of_infected_nodes_seen_by_monitors(self,IPprefix,hijacker_ASN, list_of_monitors):
		set_of_seen_infected_nodes = set()

		list_of_monitors_in_topology = [self.list_of_all_BGP_nodes[mon] for mon in list_of_monitors if mon in self.list_of_all_BGP_nodes.keys()]
		
		for node in list_of_monitors_in_topology:
			path_to_prefix = node.paths.get(IPprefix)
			if (path_to_prefix is not None) and (hijacker_ASN in path_to_prefix):
				# add the monitor to the set of seen infected nodes
				set_of_seen_infected_nodes.add(node.ASN) 
				# add all the other ASes in the infected path (in the case of a hijack type > 0: add only those after the hijacker) to the set of seen infected nodes
				hijacker_index = path_to_prefix.index(hijacker_ASN)
				for infected_ASN in path_to_prefix[0:hijacker_index]:
					set_of_seen_infected_nodes.add(infected_ASN)

		return set_of_seen_infected_nodes


	'''
	Returns the set of the nodes seen in the AS paths of the (given) monitors that have a path for the given prefix

	Finds the ASes in the given list_of_monitors that are nodes of the topology

	FOR all the considered monitors
		IF the monitor has a path to the prefix 
			THEN 	add the monitor and all nodes appearing in the path to the set_of_seen_infected_nodes

	Input arguments:
		(a) IPprefix: 		the prefix for which paths to be considered
		(b) list_of_monitors: 	the list of monitors, which will be considered

	Returns:
		A set of ASNs
	'''
	def get_set_of_nodes_seen_by_monitors(self,IPprefix,list_of_monitors):
		set_of_seen_nodes = set()

		list_of_monitors_in_topology = [self.list_of_all_BGP_nodes[mon] for mon in list_of_monitors if mon in self.list_of_all_BGP_nodes.keys()]
		
		for node in list_of_monitors_in_topology:
			path_to_prefix = node.paths.get(IPprefix)
			if path_to_prefix is not None:
				# add the monitor to the set of seen nodes
				set_of_seen_nodes.add(node.ASN) 
				# add all the other ASes in the path to the set of seen nodes
				set_of_seen_nodes.update(set(path_to_prefix))

		return set_of_seen_nodes
	


	'''
	Returns the set of the (given) nodes that have a path (for the given prefix) that includes a specific edge (i.e., sequence of two ASNs).

	IF a list_of_nodes is given:
	THEN 	consider only the list of the given nodes (that exist in the topology)
	ELSE 	consider every node in the topology

	FOR all the considered nodes
		IF the node has a path to the prefix
		THEN	IF the path contains the given edge
				THEN 	add node to the set_of_nodes_with_path_to_prefix

	Input arguments:
		(a) IPprefix: 		the prefix for which paths to be considered
		(b) edge: 			a list with two elements: the ASes between which the edge exists
		(c) list_of_nodes: 	the list of nodes, which will be considered ; default value is None (i.e., consider all the nodes of the topology)

	Returns:
		A set of ASNs
	'''
	def get_set_of_nodes_with_specific_edge_to_prefix(self,IPprefix,edge, list_of_nodes=None, directed=False):
		set_of_nodes_with_path_to_prefix = set()

		if list_of_nodes:
			list_of_nodes_to_search = {}
			for key in list_of_nodes:
				if key in self.list_of_all_BGP_nodes.keys():
					list_of_nodes_to_search[key] = self.list_of_all_BGP_nodes[key]
		else:
			list_of_nodes_to_search = self.list_of_all_BGP_nodes

		for key,node in list_of_nodes_to_search.items():
			if node.paths.get(IPprefix):
				ASN1 = edge[0]
				ASN2 = edge[1]
				path = node.paths.get(IPprefix)
				if (ASN1 in path) and (ASN2 in path): # if both ASNs exists in the path ...
					if directed:
						if (path.index(ASN1) - path.index(ASN2)) == 1:	# ... and in sequence (i.e., form an edge from ASN1 to ASN2)
							set_of_nodes_with_path_to_prefix.add(node.ASN)
					else:
						if abs(path.index(ASN1) - path.index(ASN2)) == 1:	# ... and in sequence (i.e., form an edge)
							set_of_nodes_with_path_to_prefix.add(node.ASN)

		return set_of_nodes_with_path_to_prefix


	def get_nb_of_nodes_with_specific_edge_to_prefix(self,IPprefix,edge,list_of_nodes=None, directed=False):
		return len(self.get_set_of_nodes_with_specific_edge_to_prefix(IPprefix,edge,list_of_nodes,directed))






	'''
	Writes some main information about the hijacked prefixes in the given csv file.

	(Currently) it writes to the given csv file a row per hijacked prefix.
	The format is:		nb_of_nodes_with_path_to_prefix,nb_of_nodes_with_hijacked_path_to_prefix(,nb_of_nodes_from_the_given_list_with_path_to_prefix,nb_of_nodes_from_the_given_list_with_hijacked_path_to_prefix)
				e.g., 	10,5,4,1

	Input arguments:
		(a) csv_filename: a string with the name of the csv file to be written
		(b) list_of_nodes: 	the list of the specific nodes, which will be considered; default is None
	'''
	def write_hijacking_data_to_csv(self,csv_filename,list_of_nodes=None):
		with open(csv_filename, 'w') as csvfile:
			spamwriter = csv.writer(csvfile, delimiter=',')
			for prefix,hijacker in self.get_list_of_hijacked_prefixes_and_hijackers().items():
				#print('writing statistics to csv ... '+str(100*i/nb_of_sims)+'%\r',end='')
				DATA = []
				DATA.append(self.get_nb_of_nodes_with_path_to_prefix(prefix))
				DATA.append(self.get_nb_of_nodes_with_hijacked_path_to_prefix(prefix,hijacker))
				if list_of_nodes:
					DATA.append(self.get_nb_of_nodes_with_path_to_prefix(prefix,None,list_of_nodes))
					DATA.append(self.get_nb_of_nodes_with_hijacked_path_to_prefix(prefix,hijacker,list_of_nodes))
				spamwriter.writerow(DATA)

	'''
	Adds the IXP nodes as a list to the topology class
	'''
	def load_ixps_from_json(self, json_filename):
		self.list_of_all_IXP_nodes = {}

		with open(json_filename, 'r') as jsonfile:
			raw_ixp_dict = json.load(jsonfile)

			for ixp_id, ixp_info in raw_ixp_dict.items():
				self.list_of_all_IXP_nodes[int(ixp_id)] = IXPNode(ixp_info)

		#print('%i new IXPs added in total' % (len(self.list_of_all_IXP_nodes)))

	'''
	Populates the IXP node membership info
	'''

	def load_ixp_members_from_json(self, json_filename):

		with open(json_filename, 'r') as jsonfile:
			all_asn_asn_ixp_tuples = json.load(jsonfile)

			for t in all_asn_asn_ixp_tuples:
				self.list_of_all_IXP_nodes[int(t[2])].add_ASN_member(int(t[0]))
				self.list_of_all_IXP_nodes[int(t[2])].add_ASN_member(int(t[1]))

	'''
	Add the extra IXP-based p2p links
	'''
	def add_extra_p2p_links_from_json(self, json_filename):
		with open(json_filename, 'r') as jsonfile:
			all_asn_asn_ixp_tuples = json.load(jsonfile)

		i_asn  = 0
		i_link = 0
		for t in all_asn_asn_ixp_tuples:
			if not self.has_node(t[0]) or not self.has_node(t[1]):
				i_asn += 1

			if not self.has_link(t[0],t[1]):
				self.add_link(t[0], t[1], 0)
				i_link += 1

		#print ("%i new p2p links added in total" % (i_link))
		#print ("%i new ASNs added in total because of the extra p2p links" % (i_asn))

	'''
	Implement remote peering with a certain IXP
	'''
	def peer_remotely_with_IXP(self, ASN, ixp_id):
		ixp_members = self.list_of_all_IXP_nodes[ixp_id].members

		#add the remote peer as a new IXP member
		self.list_of_all_IXP_nodes[ixp_id].add_ASN_member(ASN)

		#add the remote p2p links with all current open IXP members
		i = 0
		for member in ixp_members:
			if not self.has_link(ASN,member):
				self.add_link(ASN, member, 0)
				i += 1


		#print("%i new p2p links added due to remote peering of ASN %i with IXP %s!" %(i, ASN, ixp_id))

	'''
	Returns a list containing the IXPs (integers)
	'''
	def get_all_nodes_IXPs(self):
		return list(self.list_of_all_IXP_nodes.keys())


	'''
	Clears the routing information of all nodes in topology.
	'''
	def clear_routing_information(self,list_of_nodes=None):
		if not list_of_nodes:
			list_of_nodes = self.get_all_nodes_ASNs()
		for ASN in list_of_nodes:
			self.get_node(ASN).clear_routing_tables()
