# Copyright (C) 2015 Cisco, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Author(s): Chris Plock

"""
Openstack API cleanup utilities for Testiny.

Clients are pre-authenticated using the configuration details.
"""

from __future__ import (
    absolute_import,
    print_function,
    unicode_literals,
    )

from collections import defaultdict
import logging
import pprint
import re
from testiny.clients import get_neutron_client
from testiny.clients import get_keystone_v3_client

# a neutron_client.Client
#logging.basicConfig(level=logging.DEBUG)

pp = pprint.PrettyPrinter(indent=4)
keystone = get_keystone_v3_client()
neutron = get_neutron_client()

# TODO:
#   this means we have to track/find users/tenants/networks/routers separately
#     you can have network without a valid tenant! (presume tenant was deleted)
#     you can have users not attached to a project/tenant!
#     you can have routers not attached to a project/tenant!

# get users matching pattern
# not really sure why none of the testiny users are attached to a project though
users = [ user for user in keystone.users.list() if re.match('testiny[a-zA-Z0-9]{10}$', user.name) is not None ]

# get tenants matching pattern
projects = [ project for project in keystone.projects.list() if re.match('testiny-[a-zA-Z0-9]{10}$', project.name) is not None ]

# get networks matching name pattern
nets = [ net for net in neutron.list_networks()['networks'] if re.match('network-[a-zA-Z0-9]{10}$', net['name']) is not None ]
#pp.pprint ({ net['name']:net['id'] for net in nets })

# grab the subnets for each net and put each sublist entry in the outer list
#subnet_ids = [subnet for net in nets for subnet in net['subnets']]
#pp.pprint (subnet_ids)

# for each net, list the ports and create map of port id to the port data
# will be used to enumerate ports on subnets connected to router
#all_ports = [ port for port in neutron.list_ports()['ports'] ]
ports = [port for net in nets for port in neutron.list_ports(network_id=net['id'])['ports'] ]
ports_by_subnet = defaultdict(list)
for subnet, port in [ (fixed_ip['subnet_id'], port) for port in ports for fixed_ip in port['fixed_ips'] ]:
    ports_by_subnet[subnet].append(port)
#pp.pprint (ports)

{ fixed_ip['subnet_id'] : port for port in ports for fixed_ip in port['fixed_ips'] }

routers = [ router for router in neutron.list_routers()['routers']
    if re.match('router-[a-zA-Z0-9]{10}$', router['name']) is not None ]
#pp.pprint (routers)

all_subnets = [subnet for subnet in neutron.list_subnets()['subnets']]
all_subnets_by_id = { subnet['id'] : subnet for subnet in all_subnets }

for router in routers:
    project = next((project for project in projects
        if project.id==router['tenant_id']), None)
    # all the lists of (ip,subnet) information for all the ports attached to the router
    router_all_ports_fixed_ips = [ port['fixed_ips']
        for port in neutron.list_ports(device_id=router['id'])['ports']] 
    # the above list of lists flattened into a single list 
    router_port_fixed_ips = [ router_port_fixed_ip
        for router_port_fixed_ips in router_all_ports_fixed_ips
        for router_port_fixed_ip in router_port_fixed_ips ]
    # just the ip addresses of all the ports attached to the router
    router_ips = ', '.join([ router_port_fixed_ip['ip_address']
        for router_port_fixed_ip in router_port_fixed_ips ])
    # the subnet ids of all the ports attached to the router
    router_subnets = [ router_port_fixed_ip['subnet_id']
        for router_port_fixed_ip in router_port_fixed_ips ]
    print ('router "{}" ips: {} (project: {})'.format(router['name'], router_ips, getattr(project, 'name', None)))
    # TODO: use default_dict to collate the ips on each subnets
    # we are going to print all the ports on the router
    for router_port_fixed_ip in router_port_fixed_ips:
        # get the subnet details for the port attached to the router
        router_subnet = all_subnets_by_id[router_port_fixed_ip['subnet_id']]
        print ('    connected to subnet "{}" {} via ip {}'.format(router_subnet['name'], router_subnet['cidr'], router_port_fixed_ip['ip_address']))
        if router_subnet['tenant_id'] in [project.id for project in projects]:
	    for subnet_port in ports_by_subnet[ router_subnet['id'] ]:
		ips = [ fixed_ip['ip_address'] for fixed_ip in subnet_port['fixed_ips'] ]
	        print('        {} for {} @ {}'.format(subnet_port['device_owner'], subnet_port['binding:host_id'], ', '.join(ips)) )
        else:
	    print('        Owned by other tenant: {}', router_subnet['tenant_id'])
 
