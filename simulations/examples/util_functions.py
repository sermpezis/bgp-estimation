import numpy as np 
import matplotlib.pyplot as plt
from matplotlib import colors
import json
import csv
import random
from collections import defaultdict


'''
Calculates experimental CDF of the given data

Input: 
	data: one dimensional np.array

Return:
	cdf: the values (probablities) of the eCDF
	x:	 the values of the data that correspond to the probabilities
'''
def ecdf(data, epsilon = 0.0001):
	data = data[~np.isnan(data)]
	cdf, x = np.histogram(data, bins=np.append(np.unique(data), np.array([np.max(data)+epsilon])))
	cdf = np.cumsum(cdf)/np.sum(cdf)
	return cdf, x[0:-1]

'''
plots the cdf of the given data

Input: 
	data: one dimensional np.array
'''
def plot_cdf(data, epsilon = 0.0001,**kwargs):
	cdf, x = ecdf(data, epsilon=epsilon)
	x = np.append(x,[x[-1]+epsilon])
	cdf = np.insert(cdf,0,0)
	fig = plt.step(x,cdf,**kwargs)
	return fig

'''
plots the hist of the given data

Input: 
	data: one dimensional np.array
'''
def plot_hist(data,**kwargs):
	fig = plt.hist(data,**kwargs)
	return fig


'''
Gets the list of ASes with at least one Ripe Atlas probe from the given file.

Input:
	ripe_atlas_file: the json file with the raw data about Ripe Atlas probes
	ASes_in_topology: (optional) a list of ASes in the considered/simulated topology; if given, then only the ASes with probes that exist also in the topology are returned
	IPversion: (optional) a str {'v4','v6'} to indicate which set of probes to consider

Returns:
	ripe_atlas_ASes: a list of ASes with at least one Ripe Atlas probe

'''
def get_list_RIPE_Atlas_ASes(ripe_atlas_file, ASes_in_topology=None, IPversion='v4'):
	with open(ripe_atlas_file, 'r') as f:
		DATA = json.load(f)
	ripe_atlas_ASes = DATA[IPversion]
	if ASes_in_topology is not None:
		ripe_atlas_ASes = list( set(ripe_atlas_ASes).intersection(set(ASes_in_topology)) )
	return ripe_atlas_ASes


def get_list_monitor_ASes(monitor_file, ASes_in_topology=None):
	with open(monitor_file, 'r') as f:
		mon_ASes = json.load(f)
	if ASes_in_topology is not None:
		mon_ASes = list( set(mon_ASes).intersection(set(ASes_in_topology)) )
	return mon_ASes


def impact_dist(x,y,relative_error=True):
	if relative_error: 
		return np.array([abs(y[i]-x[i])/x[i] for i, v in enumerate(x) if v!=0 and x[i]<=1 and y[i]<=1 and x[i]>=0 and y[i]>=0]) #abs(x-y)/x
	else:
		return np.array([abs(y[i]-x[i]) for i, v in enumerate(x) if x[i]<=1 and y[i]<=1 and x[i]>=0 and y[i]>=0]) #abs(x-y)/x

def impact_mse(x,y):
	return np.array([(y[i]-x[i])**2 for i, v in enumerate(x) if v!=0 and x[i]<=1 and y[i]<=1 and x[i]>=0 and y[i]>=0])

def impact_ratio(x,y): 
	return np.array([y[i]/x[i] for i, v in enumerate(x) if v!=0])#y/x

def avg_impact_dist(*args,**kwargs):
	return np.nanmean(impact_dist(*args,**kwargs))

def median_impact_dist(*args,**kwargs):
	return np.nanmedian(impact_dist(*args,**kwargs))


def avg_impact_mse(x,y,root_mse=False):
	MSE = np.nanmean(impact_mse(x,y))
	if root_mse:
		return np.sqrt(MSE)
	else:
		return MSE

def avg_impact_ratio(*args): 
	return np.nanmean(impact_ratio(*args))


def apply_plot_formatting_impact(filename, legends, fontsize, axis=[0,1,0,1], relative_error=True):
	plt.legend(legends, fontsize=fontsize)
	plt.axis(axis)
	plt.grid(True)
	if relative_error:
		plt.xlabel('Relative error', fontsize=fontsize)
	else:
		plt.xlabel('Absolute error', fontsize=fontsize)
	plt.ylabel('CDF', fontsize=fontsize)
	plt.tick_params(labelsize=fontsize)
	plt.tight_layout()
	plt.subplots_adjust(left=0.17, bottom=0.17)
	plt.savefig(filename)
	#plt.show()
	plt.clf()





def plot_class_boundaries_2D(model, feature_names=None, fontsize=20, axes=[0,1,0,1]):
	# create a mesh to plot in
	x_min, x_max, y_min, y_max = axes
	h = 0.02  # step size in the mesh
	xx, yy = np.meshgrid(np.arange(x_min, x_max, h), np.arange(y_min, y_max, h))


	# Plot the decision boundaries and classes
	Z = model.predict(np.c_[xx.ravel(), yy.ravel()])
	Z = Z.reshape(xx.shape)
	plot = plt.contour(xx, yy, Z, colors='black', linestyles='dashed', linewidths=2)
	plt.pcolormesh(xx, yy, Z, cmap='winter', norm=colors.Normalize(0, 1), zorder=0)

	# format axis, etc.
	plt.xticks([x_min+0.2*i*(x_max-x_min) for i in range(0,6)])
	plt.yticks([y_min+0.2*i*(y_max-y_min) for i in range(0,6)])
	if feature_names is not None:
		plt.xlabel(feature_names[0], fontsize=fontsize)
		plt.ylabel(feature_names[1], fontsize=fontsize)
	e = 0.0
	plt.axis([x_min-e,x_max+e,y_min-e,y_max+e])
	plt.grid(True)

	return plot



def load_per_monitor_data(filename, shuffle_data=True, max_monitors=None, hijack_type=0):
	features_keys = ['real_impact', 'mon_impact', 'dVc', 'dHc', 'dV', 'dH', 'mon_closer_V', 'mon_closer_H', 'mon_equal_d', 'mon_impact_d0', 'mon_d1','mon_impact_d1','mon_closer_V-H']
	npDATA = np.empty((0,len(features_keys)), dtype=float)
	
	with open(filename, 'r') as f:
		cr = csv.reader(f, delimiter=',');
		for r in cr:
			features_dict = dict()
			real_impact = int(r[4])/int(r[2])	#
			features_dict['real_impact'] = real_impact
			nb_monitors_with_path = int(r[5])
			nb_monitors_infected = int(r[6])
			if (real_impact>1) or (real_impact<0) or (nb_monitors_with_path<=0) or (nb_monitors_infected<0) or (nb_monitors_infected>nb_monitors_with_path):
				continue
			
			m = []
			d = []
			dV = []
			dH = []
			dd = []
			nb_checked_monitors = 0
			MON_DATA = r[7:]
			if shuffle_data:
				random.shuffle(MON_DATA)
			for mon_data in MON_DATA:
				try:
					x = list([int(i) for i in mon_data[1:-1].split(',')])
				except ValueError:
					continue
				if (len(x)>0) and (x[2]>0) and (x[3]>0): # monitor has path to victim's AND hijacker's prefixes
					m.append( x[0])
					d.append( x[1])
					dV.append(x[2])
					dH.append(x[3])
					dd.append(x[2]-x[3])

				nb_checked_monitors +=1
				if (max_monitors is not None) and (nb_checked_monitors >= max_monitors):
					break
			if len(m) ==0: 
				continue

			m,d,dV,dH,dd = map(lambda x: np.array(x),  [m,d,dV,dH,dd])
			V_ind = np.where(m==0)
			H_ind = np.where(m==1)
			nb_monitors = len(m)
			features_dict['mon_impact'] = 1.0*len(H_ind[0])/nb_monitors if nb_monitors>0 else np.nan	#
			features_dict['dVc'] = np.mean(d[V_ind]) if len(V_ind[0])>0 else np.nan	#
			features_dict['dHc'] = np.mean(d[H_ind]) if len(H_ind[0])>0 else np.nan		#
			features_dict['dV'] = np.mean(dV)	#
			features_dict['dH'] = np.mean(dH)	#
			features_dict['mon_closer_V'] = 1.0*len(np.where(dd<-hijack_type)[0])/nb_monitors if nb_monitors>0 else np.nan	#
			features_dict['mon_closer_H'] = 1.0*len(np.where(dd>-hijack_type)[0])/nb_monitors if nb_monitors>0 else np.nan	#
			d0_ind = np.where(dd==-hijack_type)
			features_dict['mon_equal_d']  = 1.0*len(d0_ind[0])/nb_monitors if nb_monitors>0 else np.nan	#
			nb_mon_d0 = len(d0_ind[0])
			features_dict['mon_impact_d0'] = 1.0*sum(m[d0_ind])/nb_mon_d0 if (nb_mon_d0 > 0) else np.nan	#
			d1_ind = np.where(np.abs(dd+hijack_type)<=1)
			nb_mon_d1 = len(d1_ind[0])
			features_dict['mon_d1']  = 1.0*nb_mon_d1/nb_monitors if nb_monitors>0 else np.nan	#
			features_dict['mon_impact_d1'] = 1.0*sum(m[d1_ind])/nb_mon_d1 if (nb_mon_d1 > 0) else np.nan	#
			features_dict['mon_closer_V-H'] = features_dict['mon_closer_V'] - features_dict['mon_closer_H']	#

			npDATA = np.vstack((npDATA, np.array([features_dict[k] for k in features_keys])))

	return npDATA




def get_impact_dict_from_data(data, max_monitors=None):
	impact_dict = defaultdict(defaultdict)
	impact_dict_RC = defaultdict(defaultdict)
	for infected in [0,1]:
		for dd in [-1,0,1]:
			impact_dict[infected][dd] = defaultdict()
			impact_dict_RC[infected][dd] = defaultdict()

	i = 5
	for infected in [0,1]:
		for dd in [-1,0,1]:
			for nn in [-1,0,1]:
				impact_dict[infected][dd][nn] = data[:,i]
				i += 1
	for infected in [0,1]:
		for dd in [-1,0,1]:
			for nn in [-1,0,1]:
				impact_dict_RC[infected][dd][nn] = data[:,i]
				i += 1

	if max_monitors is not None:
		total_nb_RC = 0
		impact_dict_RC_NEW = defaultdict(defaultdict)
		for infected in [0,1]:
			for dd in [-1,0,1]:
				impact_dict_RC_NEW[infected][dd] = defaultdict()
				for nn in [-1,0,1]:
					total_nb_RC += impact_dict_RC[infected][dd][nn]
					impact_dict_RC_NEW[infected][dd][nn] = np.zeros_like(impact_dict_RC[infected][dd][nn])
		for i in range(len(total_nb_RC)):
			if max_monitors > total_nb_RC[i]:
				continue
			s = set(random.sample(range(total_nb_RC[i]), max_monitors))
			ss = 0
			for infected in [0,1]:
				for dd in [-1,0,1]:
					for nn in [-1,0,1]:
						impact_dict_RC_NEW[infected][dd][nn][i] += len( set([x+ss for x in range(impact_dict_RC[infected][dd][nn][i])]).intersection(s) )
						ss += impact_dict_RC[infected][dd][nn][i]
		impact_dict_RC = impact_dict_RC_NEW


	return impact_dict, impact_dict_RC



def get_customer_cone_size(Topo, list_of_ASes):
	customer_cone_sizes = []
	for AS in list_of_ASes:
		current_customer_cone = set()
		ASes_to_check = set([AS])
		checked_ASes = set()
		while len(ASes_to_check)>0:
			next_AS_to_check = ASes_to_check.pop()
			checked_ASes.add(next_AS_to_check)
			if Topo.has_node(next_AS_to_check):
				current_customers = Topo.get_node(next_AS_to_check).get_neighbors()['customers']
				ASes_to_check.update(set(current_customers)-checked_ASes)
		customer_cone_sizes.append(len(checked_ASes))
	return customer_cone_sizes


def get_tier_type(Topo, list_of_ASes):
	tier_types = []
	nb_of_neighbors = []
	for AS in list_of_ASes:
		if Topo.has_node(AS):
			neighbors = Topo.get_node(AS).get_nb_of_neighbors()
			if neighbors[2] == 0:
				tier_types.append(3)	# stub AS (or, tier-2 AS)
			elif neighbors[0] == 0:
				tier_types.append(1)	# tier-1 AS
			else:
				tier_types.append(2)	# tier-2 AS
			nb_of_neighbors.append(sum(neighbors))
		else:
			tier_types.append(3)
			nb_of_neighbors.append(0)
	return tier_types, nb_of_neighbors
