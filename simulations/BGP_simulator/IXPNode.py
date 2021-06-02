#!/usr/bin/env python3
#
#
# Author: Vasileios Kotronis
# Institute of Computer Science, Foundation for Research and Technology - Hellas (FORTH), Greece
#
# E-mail: vkotronis@ics.forth.gr
#
#
# This file is part of the BGPsimulator
#

from pprint import pprint as pp

class IXPNode:
    '''
    Class for IXP nodes

    Class variables:
        (a) id                  : integer,example : 986,
        (b) name                : string, example : 'MidWest-IX',
        (c) name_long           : string, example : 'Midwest Internet Exchange Indy',
        (d) city                : string, example : 'Indianapolis, Indiana',
        (e) country             : string, example : 'US',
        (f) region_continent    : string, example : 'North America',
        (g) status              : string, example : 'ok',
        (h) website             : string, example: 'http://www.midwest-ix.com'
        (i) members             : list of ASNs that are members with this IXP (under open policy)

    Input arguments:
		raw_dict: dictionary with all the ixp related data from peeringdb
    '''

    def __init__(self, raw_dict):
        self.id                 = int(raw_dict['id'])
        self.name               = raw_dict['name']
        self.name_long          = raw_dict['name_long']
        self.city               = raw_dict['city']
        self.country            = raw_dict['country']
        self.region_continent   = raw_dict['region_continent']
        self.status             = raw_dict['status']
        self.website            = raw_dict['website']
        self.members            = set([])

    def add_ASN_member(self, ASN):
        self.members.add(ASN)

    def remove_ASN_member(self, ASN):
        self.members.remove(ASN)

    ### methods for	printing information ###
    def print_info(self):
        print('***IXP***: '     +str(self.id))
        print('ID = '           + str(self.id))
        print('Name = '         + str(self.name))
        print('Long Name = '    + str(self.name_long))
        print('City = '         + str(self.city))
        print('Country = '      + str(self.country))
        print('Reg / cont. = '  + str(self.region_continent))
        print('Status = '       + str(self.status))
        print('Website = '      + str(self.website))
        print('Members = ')
        pp(self.members)
        print(' ')
