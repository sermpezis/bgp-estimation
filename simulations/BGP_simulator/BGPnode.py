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


import random
from collections import defaultdict
from copy import deepcopy

class BGPnode:
	''' 
	Class for BGP nodes (i.e., ASes are represented as single nodes). 
	A BGPnode can own IP prefixes, have connections to other BGPnodes/ASes.
	In this class, there exist methods related to the IPprefixes, AS connections, and methods for exchanging BGP messages (announcing, receiving, propagating, hijacking).

	class variables: 
		(a) ASN: 				integer (mandatory, given upon creation) - id of the node corresponding to its AS number
		(b) Topology: 			object of type BGPtopology (mandatory, given upon creation) - object/topology to which the node belongs
		(c) IPprefix: 			set (initially empty) - set of prefixes owned by the BGPnode
		(d) hijacked_IPprefix: 	dictionary (initially empty) - dictionary with (i) keys the hijacked IP prefixes and (ii) values the hijack_type as int (0==origin_AS hijack, 1== 1st hop hijack, etc. )
		(e) ASneighbors: 		dictionary (initially empty) - dictionary with (i) keys the ASNs of neighbors and (ii) values {1,0,-1} if the neighbor is {provider,peer,customer} respectively
		(f) ASneighbors_preference: 	dictionary (initially empty) - dictionary with (i) keys the ASNs of neighbors and (ii) values the preferences of the neighbors for selection of BGP paths / tie breaker - values are float in [0,1]
		(g) paths:				dictionary (initially empty) corresponding to the best paths per prefix - dictionary with (i) keys the IP prefixes and (ii) values the corresponding AS path given as a list (e.g., [ASNx, ASNy, ASNz, origin_ASN])
		(h) all_paths:			dictionary of dictionaries (initially empty) representing the local FIB of BGP - dictionary with (i) keys the IP prefixes, (ii) keys (for each prefix) the ASN of the neighbor that sent the path, and (iii) values the corresponding AS path given as a list (e.g., [ASNx, ASNy, ASNz, origin_ASN])
		(i) filters:			dictionary (initially empty) - dictionary with (i) keys the IPprefixes, and (ii) values sets of ASNs; if an ASN exists in the set, then the every path for the prefix that contains this ASN need to be filtered/discarded
	'''

	'''
	Contructor for object of the class BGPnode. Creates the class variables from the given arguments, and defines the variable types for the initially epmty class variables.

	Input arguments:
		(a) ASN:		integer
		(b) Topology:	object of type BGPtopology
	'''
	def __init__(self, ASN, Topology):
		self.ASN = ASN
		self.Topology = Topology 
		self.IPprefix = set()	
		self.hijacked_IPprefix = {}
		self.ASneighbors = {}
		self.ASneighbors_preference = {}
		self.paths = {} 
		self.all_paths = defaultdict(dict)
		self.filters = {}


	
	### methods for owned prefixes ###

	'''
	Adds the given prefix to the dictionary ("IPprefix" class variable) for the owned prefixes.
	
	IF the given prefix does not exist in the "IPprefix" dictionary, 
	THEN 	(i) add the prefix, 
			(ii) set an empty path for this prefix in the "paths" dictionary, and
			(iii) announce the prefix

	Input argument:
		(a) IPprefix: the (owned) prefix to be added
	'''
	def add_prefix(self,IPprefix,forbidden_neighbors=None):
		if not self.has_prefix(IPprefix):
			self.IPprefix.add(IPprefix)
			self.paths[IPprefix] = []
			if forbidden_neighbors is not None:
				neighb_to_announce = set(self.ASneighbors.keys()).difference(set(forbidden_neighbors))
				self.announce_path(IPprefix,list(neighb_to_announce))
			else:
				self.announce_path(IPprefix,list(self.ASneighbors.keys()))
	'''
	Re-announces the given prefix, if it is an owned or hijacked prefix.
	
	IF the given prefix is an owned or hijacked prefix, 
	THEN 	announce the prefix (as owned, or the fake/hijacked path) to all neighbors

	Input argument:
		(a) IPprefix: the prefix to be re-announced
	'''
	def re_announce_prefix(self,IPprefix):
		if self.has_prefix(IPprefix) or self.has_hijacked_prefix(IPprefix):
			self.announce_path(IPprefix,list(self.ASneighbors.keys()))

	'''
	Checks if the given prefix exists in the "IPprefix" dictionary.
	
	Returns:
		TRUE if it exists, FALSE otherwise
	'''
	def has_prefix(self,IPprefix):
		if IPprefix in self.IPprefix:
			return True
		else:
			return False

	'''
	Returns:
		The dictionary "IPprefix"
	'''
	def get_prefixes(self):
		return self.IPprefix


	'''
	Clears the routing tables, i.e. the dictionaries "paths" and "all_paths"
	'''
	def clear_routing_tables(self):
		# self.paths.clear() #self.paths = {} 
		# self.all_paths.clear() #self.all_paths = defaultdict(dict)
		# self.IPprefix.clear()	
		# self.hijacked_IPprefix.clear()
		# self.filters.clear()		
		self.paths = {} 
		self.all_paths = defaultdict(dict)
		self.IPprefix = set()
		self.hijacked_IPprefix = {}
		self.filters = {}
		

	### methods for	hijacked IP prefixes ###

	'''
	Adds the given prefix and the corresponding hijack type to the dictionary ("hijacked_IPprefix" class variable) for the hijacked prefixes.
	
	IF the given prefix does not exist in the "hijacked_IPprefix" dictionary, 
	THEN 	(i) add the prefix as the key to the "hijacked_IPprefix" dictionary, and 
			(ii) set the corresponding value of the dictionary equal to the hijack type
	
	Input argument:
		(a) IPprefix: the (hijacked) prefix to be added
		(b) hijack_type: the type of the hijack for this prefix
	'''
	def add_hijacked_prefix(self,IPprefix,hijack_type):
		if not self.has_prefix(IPprefix):
			self.hijacked_IPprefix[IPprefix] = hijack_type
			# the best path of the hijacker remains as before the hijacking (i.e., the legitimate path); however, the hijacker does not propagate legitiamte paths for her own hijacked prefixes. 
			# I.e., do NOT add the following line (it creates a problem in the method "get_path_poisoning_hijack(...)" ) 
			# the self.paths[IPprefix] = []

	'''
	Checks if the given prefix exists in the "hijacked_IPprefix" dictionary.
	
	Input argument:
		(a) IPprefix: the prefix to be checked

	Returns:
		TRUE if it exists, FALSE otherwise
	'''
	def has_hijacked_prefix(self,IPprefix):
		if IPprefix in self.hijacked_IPprefix.keys():
			return True
		else:
			return False

	'''
	Returns:
		The dictionary "hijacked_IPprefix"
	'''
	def get_hijacked_prefixes(self):
		return self.hijacked_IPprefix



	### methods for	AS neighbors ###

	'''
	Adds the given ASN and the corresponding peering relation type to the dictionary ("ASneighbors" class variable) for the AS neighbors, and sets a random value for the preference for this AS neighbor.
	
	IF the given ASN does not exist in the "ASneighbors" dictionary, 
	THEN 	(i) add the ASN as the key to the "hijacked_IPprefix" dictionary, 
			(ii) set the corresponding value of the dictionary equal to the given peering relation type, and
			(iii) set a random value (float in the range [0,1]) for the preference for this AS neighbor (to be used for BGP tie breaker)
	
	Input arguments:
		(a) ASN: the AS number of the AS neighbor to be added
		(b) relation: a string that denotes the peering relation type with the AS neighbor; IF ""
	'''
	def add_ASneighbor(self,ASN,relation):
		if not self.has_ASneighbor(ASN): 
			if relation == 'customer':
				self.ASneighbors[ASN] = -1
			elif relation == 'peer':
				self.ASneighbors[ASN] = 0
			elif relation == 'provider':
				self.ASneighbors[ASN] = 1
			else:
				print('ERROR: Not valid peering relation')
			self.ASneighbors_preference[ASN] = random.random()	# add a random preference to neighbor
	

	def remove_ASneighbor(self,ASN):
		if self.has_ASneighbor(ASN): 
			del self.ASneighbors[ASN]
			del self.ASneighbors_preference[ASN]
			# for prefix in self.all_paths.keys():
			# 	self.withdraw_path(prefix,ASN)
	
	'''
	Checks if the AS neighbor exists in the "ASneighbors" dictionary.
	
	Returns:
		TRUE if it exists, FALSE otherwise
	'''
	def has_ASneighbor(self,ASN):
		if ASN in self.ASneighbors.keys():
			return True
		else:
			return False

	'''
	Returns the number of neighbors, grouped by type.

	Create a new dictionary with keys the type of neighbor, i.e., {1,0,-1} for {providers, peers, customers} respectively, and values the list of neighbors of this type.

	Returns:
		A tuple {nb_of_providers, nb_of_peers, nb_of_customers}
	'''
	def get_nb_of_neighbors(self):
		neighbor_type_dict = defaultdict(list)
		for ASN, type in self.ASneighbors.items():
		    neighbor_type_dict[type].append(ASN)
		return list([len(neighbor_type_dict[1]), len(neighbor_type_dict[0]), len(neighbor_type_dict[-1])])

	'''
	Returns the list of neighbors, grouped by type.

	Create a new dictionary with keys the type of neighbor, i.e., {1,0,-1} for {providers, peers, customers} respectively,
	and values the list of neighbors of this type.

	Returns:
		A dictionary {'providers' : list_of_providers, 'peers' : list_of_peers, 'customers' : list_of_customers}
	'''
	def get_neighbors(self):
		neighbor_type_dict = defaultdict(list)
		for ASN, type in self.ASneighbors.items():
		    neighbor_type_dict[type].append(ASN)
		return {'providers': neighbor_type_dict[1],
				'peers': neighbor_type_dict[0],
				'customers': neighbor_type_dict[-1]}

	'''
	Returns the best path (i.e. value in the "paths" dictionary) for the given prefix

	Input argument:
		(a) IPprefix:	the prefix the path to which is requested

	Returns:
		A path, i.e., a list of ASNs, for the given prefix
	'''
	def get_path(self,IPprefix):
		return self.paths.get(IPprefix)

	### methods for	BGP paths (reception, announcement, updating, propagation, etc.) ###

	'''
	Receives a BGP announcement for a BGP path (i.e., a prefix and the corresponding AS path), and -if necessary- changes the entry for the path and propagates the path.

	Calls the method "conditions_to_add_received_path(...)" to decide if the received announcement must trigger further actions.
	IF "conditions_to_add_received_path(...)" returns TRUE,
	THEN 	IF the announcement must be filtered (i.e., illegitimate path)
			THEN 	calls the method "withdraw_path(...)" to discard all the illegitimate paths and withraw (if needed) all the needed paths
			ELSE 	(i) calls the method "add_received_path(...)" to add the given path in the "all_paths" dictionary (i.e. local BGP FIB), and update the entry in the dictionary "paths" for the given prefix, and
					(ii) IF the method "add_received_path(...)" returns TRUE (i.e., the given path is selected as the best path)
				 		 THEN 	call the method "export_path(...)" to export the given path

	Input arguments:
		(a) IPprefix:	the prefix of the received BGP announcement
		(b) new_path:	the path (i.e., list of ASNs) for the prefix, of the received BGP announcement
	'''
	def receive_path(self,IPprefix, new_path):
		if self.conditions_to_add_received_path(IPprefix,new_path):
			if self.must_filter_path(IPprefix,new_path) or (self.ASN in new_path):
				self.withdraw_path(IPprefix,new_path[0])
			else:
				bool_export_path = self.add_received_path(IPprefix,new_path)
				if bool_export_path:
					self.export_path(IPprefix)


	'''
	Decides if the given path is should be considered to for further actions (e.g., to be added in the local FIB / "all_paths" dictionary, or selected as the best path) or discarded.

	IF the given prefix is not (i) an owned or (ii) hijacked prefix, and (iii) the new path does not contain my ASN (for loop avoidance),
	THEN 	return TRUE
	ELSE 	return FALSE  (i.e., the received path for the prefix must be discarded)

	Input arguments:
		(a) IPprefix:	the prefix for which the new path is received and needs to be checked
		(b) new_path:	the path (i.e., list of ASNs) for the prefix that needs to be checked

	Returns:
		TRUE if the path for the prefix should be considered for further actions, FALSE otherwise (i.e. discard it)
	''' 
	def conditions_to_add_received_path(self,IPprefix,new_path):
		if (not self.has_prefix(IPprefix)) and (not self.has_hijacked_prefix(IPprefix)):	# if it's (a) not my prefix, AND (b) not a prefix I have hijacked, ADN (c) the new path does not contain my ASN (i.e., for loop avoidance) 
			return True
		return False


	'''
	Adds the given path for the given prefix in the "all_paths" dictionary (i.e., local BGP FIB), and compares the given path with the with the stored best path (if any) for the given prefix, and decides if the new path needs to replace the stored path (or added if no stored path exists).

	Adds the given path in the "all_paths" dictionary (for the keys: given prefix and neighbor that sent the path "new_path[0]"); in case a stored path for this prefix from this neighbor exists, replaces the stored path with the given path.
	IF a path for the given prefix exists,
	THEN 	IF the existing best path is from the same neighbor as the given path, 
			THEN 	set as the existing best path the given path, and select the best path among all the stored paths in the "all_paths" dictionary (i.e., select from all paths in the local BGP FIB),
					and return TRUE
			ELSE 	IF the given path is preferred than the existing best path, set the given path as the best path,
					and return TRUE
	ELSE 	set the given path as the best path (i.e., in the "paths" dictionary), 
			and return TRUE

	Input arguments:
		(a) IPprefix:	the prefix for which the new path is received and is to be added in the local FIB and considered for best path 
		(b) new_path:	the path (i.e., list of ASNs) that is received and is to be added in the local FIB and considered for best path

	Returns:
		TRUE if the path for the prefix in the "paths" dictionary needs to be changed, FALSE otherwise
	''' 
	def add_received_path(self,IPprefix,new_path):
		self.all_paths[IPprefix][new_path[0]] = new_path # replace or add the path from this neighbor (new_path[0])
		if self.paths.get(IPprefix):
			my_best_path = list(self.paths[IPprefix])
			if new_path[0] == my_best_path[0]:
				self.paths[IPprefix] = new_path
				self.select_best_path(IPprefix)
				return True
			else:
				if self.conditions_to_change_existing_path(IPprefix,new_path):
					self.paths[IPprefix] = new_path
					return True
		else:
			self.paths[IPprefix] = new_path
			return True
		return False


	'''
	Selects the best path for the given prefix among all the paths in the "all_paths" dictionary, and sets this path as best path in the "paths" dictionary

	IF no best path exists for the given prefix, 
	THEN 	IF there exists at least one path in the "all_paths" dictionary
			THEN 	select randomly one of the paths in the "all_paths" dictionary as best path (i.e., put it in the "paths" dictionary)
			ELSE 	set the best path equal to an empty path/list

	FOR EACH path in the "all_paths" dictionary, compare the path with the current best path, and select the best path among the two. 
		In the end, the "paths" dictionary contains the best path among the paths in the "all_paths" dictionary.

	Input argument:
		(a) IPprefix:	the prefix for which a best path is to be selected 
	'''
	def select_best_path(self,IPprefix):
		if not self.paths.get(IPprefix):
			if self.all_paths.get(IPprefix):
				self.paths[IPprefix] = random.choice(list(self.all_paths[IPprefix].values()))
			else:
				self.paths[IPprefix] = []
		for search_path in self.all_paths[IPprefix].values(): # finds the best path and adds it to the self.paths[IPprefix]
			if self.conditions_to_change_existing_path(IPprefix,search_path):
				self.paths[IPprefix] = search_path




	'''
	Adds a filter for the received announcements for the given prefix that contain (in the path) the given ASN, removes all stored paths ("all_paths" dictionary) that do not conform to the new filter, and withdraws any previous announcements affected by the new filter.

	Adds the given filter in the "filter" dictionary.
	IF a path for the given prefix exists
	THEN 	(i) FOR EACH stored path in the "all_paths" dictionary, remove the path if it must be filtered (using the method "must_filter_path(...)")
			(ii) IF the existing best path must be filtered
				 THEN 	call the method "withdraw_path(...)" to witdraw all previous announcements that do not conform to the filter.

	Input arguments:
		(a) IPprefix:	the prefix for which the filtering will be enabled 
		(b) ASN:		the filter, i.e., the ASN whose announcements for the given prefix will be filtered out 
	'''
	def filter_path(self,IPprefix,ASN):
		self.add_filter(IPprefix,ASN)
		if self.paths.get(IPprefix):	
			copy_of_all_paths = deepcopy(self.all_paths[IPprefix])	
			for search_key,search_path in copy_of_all_paths.items():
				if self.must_filter_path(IPprefix,search_path):
					del self.all_paths[IPprefix][search_key]
			my_best_path = list(self.paths[IPprefix])		
			if self.must_filter_path(IPprefix,my_best_path): 
				self.withdraw_path(IPprefix,my_best_path[0])

	'''
	Removes all the stored paths in the "all_paths" dictionary from the given AS for the given prefix, and if any of them is the best path, then (i) withdraws also the previous announcement of the existing best path, and (ii) selects and announces the new best path.

	IF a path exists in the "paths" dictionary for the given prefix
	THEN 	(i) IF a path exists in the "all_paths" dictionary for the given prefix from the given AS
			    THEN remove this path from the "all_paths" dictionary
			(ii) IF the existing path in the "paths" dictionary (i.e., the best path) is from the given AS
				 THEN 	(a) withdraw the announced paths from all neighbors
				 		(b) select a new best path
				 		(c) export the new best path to the neighbors

	Input arguments:
		(a) IPprefix:	the prefix for which the path will be withdrawn 
		(b) w_ASN:		the neighbor AS (i.e., the last AS in the path; not necessarily the origin-AS) that announced the path which will be withdrawn 
	'''
	def withdraw_path(self,IPprefix,w_ASN):		# withdraws path without announcing a new path for this prefix
		if self.paths.get(IPprefix):	# if a path for this prefix exists in my FIB
			if self.all_paths[IPprefix].get(w_ASN):
				del self.all_paths[IPprefix][w_ASN]		# remove it from local FIB
			if w_ASN == list(self.paths[IPprefix])[0]:	# if the withdrawn path is my current best path
				for neighbor in self.ASneighbors.keys(): # make all my neighbors to withdraw the path (in case I have announced it to them)
					self.Topology.get_node(neighbor).withdraw_path(IPprefix,self.ASN)	# do withdrawal to neighbor
				self.paths[IPprefix] = []	# remove it from my best path
				self.select_best_path(IPprefix)	# select a new best path
				if self.paths.get(IPprefix):
					self.export_path(IPprefix)	# export the new best path


	'''
	Adds a filter for the given prefix.

	IF there are filters for the given prefix
	THEN 	add the given ASN in the set of filters for the given prefix (if the filter exists, there will be no change, since the filters are stored in a set)
	ELSE 	add to the dictionary a filter for the given prefix and add to it the given ASN

	Input arguments:
		(a) IPprefix:	the prefix for which the filter will be added 
		(b) ASN:		the filter, i.e., the ASN whose announcements for the given prefix will be filtered out 
	'''
	def add_filter(self,IPprefix,ASN):
		if self.filters.get(IPprefix):
			self.filters[IPprefix].add(ASN)
		else:
			self.filters[IPprefix] = set([ASN])

	'''
	Checks if the received path must be filtered, based on the stored filters.
	
	IF a filter for the given prefix exists
	THEN 	FOR EACH ASN in the given path
				IF the ASN exists in the filter for the given prefix (i.e. the dictionary "filters")
				THEN 	return True (i.e., filter the path)

	Input arguments:
		(a) IPprefix:	the prefix for which the path has to be checked if it will be filtered 
		(b) path:		the path (i.e., list of ASNs) which will be checked if it will be filtered

	Returns:
		TRUE if the path must be filtered, FALSE otherwise
	'''
	def must_filter_path(self,IPprefix,path):
		if self.filters.get(IPprefix):
			for ASN in path:
				if ASN in self.filters[IPprefix]:
					return True
		return False

	'''
	### NOT USED METHOD ###
	Compares the given path for the given prefix with the stored path (if any) for the given prefix, and decides if the new path needs to replace the stored path (or added if no stored path exists).

	IF the given prefix is not an owned or hijacked prefix, and the new path does not contain my ASN (for loop avoidance),
	THEN 	IF there exists a stored path in the dictionary "paths" for the given prefix, 
			THEN 	call method "conditions_to_change_existing_path(...)" to check if the existing paths needs to be changed,
			ELSE 	return TRUE (i.e., the path for the prefix in the "paths" dictionary needs to be added/changed)
	ELSE 	return FALSE  (i.e., the path for the prefix in the "paths" dictionary must not be added/changed)

	Input arguments:
		(a) IPprefix:	the prefix for which there exists a new path 
		(b) new_path:	the path (i.e., list of ASNs) for the prefix

	Returns:
		TRUE if the path for the prefix in the "paths" dictionary needs to be added/changed, FALSE otherwise
	''' 
	def change_path(self,IPprefix,new_path):
		if (not self.has_prefix(IPprefix)) and (not self.has_hijacked_prefix(IPprefix)) and (self.ASN not in new_path):	# if it's (a) not my prefix, AND (b) not a prefix I have hijacked, ADN (c) the new path does not contain my ASN (i.e., for loop avoidance) 
			if self.paths.get(IPprefix):		# (if) I already have a path for this prefix in my table
				if self.conditions_to_change_existing_path(IPprefix, new_path):
					return True					
			else:					# (else) I do NOT have a path for this prefix in my table
				return True
		return False
	
	'''
	Defines and checks the conditions that must be satisfied in order to replace an existing path for a prefix.

	IF the given path is from the same neighbor as the existing path, 
	THEN 	change the path (because this neighbor would withdraw the old path in practice)

	IF the given path is from a customer (or, peer) AS neighbor, and the existing path is from a peer/provider (or, provider) AS neighbor, 
	THEN 	return TRUE (i.e., prefer the given path)
	ELIF the given and existing paths are from same type of AS neighbors,
	THEN 	(i) prefer the shorter path, or
			(ii) if both paths are of equal length, prefer the path from the neighbor with the higher preference
	ELSE 	return FALSE (i.e., prefer the existing path)


	Input arguments:
		(a) IPprefix:	the prefix for which there exists a new path 
		(b) new_path:	the path (i.e., list of ASNs) for the prefix

	Returns:
		TRUE if the path for the prefix in the "paths" dictionary needs to be replaced, FALSE otherwise
	'''
	def conditions_to_change_existing_path(self,IPprefix, new_path):
		my_path = list(self.paths[IPprefix])
		if new_path[0] == my_path[0]: 	# if the new path is from the same neighbor as the old path, then change the path (because this neighbor would withdraw the old path in practice)
			return True 
		if self.ASneighbors[new_path[0]] < self.ASneighbors[my_path[0]]:	# Prefer customer (-1) > peer (0) > provider (1)
			return True
		elif self.ASneighbors[new_path[0]] == self.ASneighbors[my_path[0]]:	# if both paths from equal neighbors ...
			if len(new_path) < len(my_path):	# if new path is shorter ...prefer it
				return True
			elif len(new_path) == len(my_path):	# if new path is of equal length ...
				return self.ASneighbors_preference[new_path[0]] > self.ASneighbors_preference[my_path[0]]	# ... return neighbor with highest preference
		return False

	'''
	Exports the path for the given prefix, i.e., (i) selects to which neighbors the path for the given prefix needs to be announced, and (ii) sends them the announcement.

	IF the path for the given prefix is from a customer AS neighbor,
	THEN 	the path must be announced to all AS neighbors (expect for the neighbor that sent it)
	ELSE 	the path must be announced to all customer AS neighbors

	Input arguments:
		(a) IPprefix:	the prefix whose the path needs to be exported
	'''
	def export_path(self,IPprefix):
		neighbors_to_announce = set()
		#neighbor_who_sent_the_announcement = self.ASneighbors[self.paths[IPprefix][0]]
		neighbor_who_sent_the_announcement = self.paths[IPprefix][0]
		if  self.ASneighbors[neighbor_who_sent_the_announcement] == -1:	# (if) path received from customer .... announce to all
			neighbors_to_announce = set(self.ASneighbors.keys())
		else:				# (else) path received from peer/provider ... announce to all customers 
			for asn,peer_type in self.ASneighbors.items():
				if peer_type == -1:
					neighbors_to_announce.add(asn)
		neighbors_to_announce.discard(neighbor_who_sent_the_announcement)	# do NOT announce to the neighbor from which the path is received
		if neighbors_to_announce:
			self.announce_path(IPprefix, neighbors_to_announce)

	'''
	Announces the path for the given prefix to the given set of AS neighbors. 

	IF a certain path is not given
	THEN 	(i) get the path that is stored in the "paths" dictionary, and
			(ii) add to it the self.ASN
	Announce the (given/stored) path to the given AS neighbors
	'''
	def announce_path(self,IPprefix, neighbors_to_announce, path_to_announce=None):
		if path_to_announce is None:
			path_to_announce = list(self.paths[IPprefix])
			path_to_announce.insert(0,self.ASN)
		for neighbor in neighbors_to_announce:
			self.Topology.get_node(neighbor).receive_path(IPprefix,path_to_announce)	# do announcement to neighbor





	### methods for	hijacking ###

	'''
	Hijacks the given prefix  (i.e., announces a path that -illegitimately- includes the self.ASN).

	IF the given prefix is NOT an owned prefix or a prefix previously hijacked,
	THEN 	(i) add the given prefix to the dictionary of the hijacked prefixes,
			(ii) IF the hijack type is 0 (i.e. origin AS hijack)
				 THEN 	set the path to be announced equal to [self.ASN]
				 ELSE 	call the method "get_path_poisoning_hijack(...)" to set the path
			(iii) set the path in the "paths" dictionary equal to the announced/hijacked/fake path (without the self.ASN)
			(iv) announce the path to all neighbors

	Input arguments:
		(a) IPprefix:		the prefix to be hijacked
		(b) hijack_type: 	the type of the hijack attack; the default value is 0, which corresponds to an origin-AS hijack
	'''
	def do_hijack(self, IPprefix, hijack_type=0):
		if (not self.has_prefix(IPprefix)) and (not self.has_hijacked_prefix(IPprefix)):
			self.add_hijacked_prefix(IPprefix,hijack_type)
			neighbors_to_announce = set(self.ASneighbors.keys())	# announce the hijack to all neighbors
			if hijack_type == 0: 	# origin-AS
				path_to_announce = [self.ASN]					
			else:					# 1st, 2nd, 3rd, etc. hop hijack, where hijack_type = 1,2,3,etc.
				path_to_announce = self.get_path_poisoning_hijack(IPprefix, hijack_type)
			self.paths[IPprefix] = path_to_announce[1:]
			if len(path_to_announce):	# check for the case that the "self.get_path_poisoning_hijack(...)"" function returns an empty list
				self.announce_path(IPprefix, neighbors_to_announce, path_to_announce)



	'''
	Returns the path to be announced for a hijack of type {1,2,3,...} (i.e., a not origin-AS hijack).

	(For the moment) this method does path poisoning as follows:
	IF the hijacker AS has an existing/stored path for the given prefix,
	THEN 	IF the length of the stored path is less than the attack type 
			THEN 	use the first hops in the stored AS path, e.g., if the hijacker has the path [AS3 AS2 AS1 origin_AS] and wants to do 2nd hop hijack, she will announce the path [self.ASN AS1 origin_AS]
			ELSE 	complete first hops with origin ASN, e.g., for 2nd hop hijack announce [hijacker_AS origin_AS origin_AS]
	ELSE do nothing (TODO: create a hijack-path for the given prefix when there is no stored legitimate-path)

	Input arguments:
		(a) IPprefix:		the prefix to be hijacked
		(b) hijack_type: 	the type of the hijack attack

	Returns:
		An AS-path, i.e., a list of ASNs (integers)
	'''
	def get_path_poisoning_hijack(self, IPprefix, hijack_type):
		if self.paths.get(IPprefix):
			original_path = list(self.paths.get(IPprefix))
			if  hijack_type <= len(original_path):
				path_to_announce = [self.ASN] + original_path[-hijack_type:]
			else:
				path_to_announce = [self.ASN] + [original_path[-1]]*hijack_type
		else:
			# TODO: create a hijack-path for the given prefix when there is no stored legitimate-path
			path_to_announce = []
		return path_to_announce
		



	### methods for	printing information ###

	def print_info(self):
		print('***ASN***: '+str(self.ASN))
		if self.IPprefix:
			print('IP prefixes: '+str(self.IPprefix))
		if self.hijacked_IPprefix:
			print('hijacked IP prefixes: '+str(set(self.hijacked_IPprefix.keys())))
		if self.ASneighbors:
			print('AS neigbors')
			for asn,peer_type in self.ASneighbors.items():
				print(str(asn)+':'+str(peer_type))
		if self.paths:
			for ip,p in self.paths.items():
				print('IP: '+str(ip)+'   path: '+str(p))
		print(' ')
