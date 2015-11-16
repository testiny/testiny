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
subnet_ids = [subnet for net in nets for subnet in net['subnets']]
#pp.pprint (subnet_ids)

# for each net, list the ports and create map of port id to the port data
ports = [port for net in nets for port in neutron.list_ports(network_id=net['id'])['ports'] ]
#pp.pprint (ports)

routers = [ router for router in neutron.list_routers()['routers']
    if re.match('router-[a-zA-Z0-9]{10}$', router['name']) is not None ]
#pp.pprint (routers)

all_subnets = [subnet['id'] for subnet in neutron.list_subnets()['subnets']]

for router in routers:
    project = next((project for project in projects
        if project.id==router['tenant_id']), None)
    router_all_ports_fixed_ips = [ port['fixed_ips']
        for port in neutron.list_ports(device_id=router['id'])['ports']] 
    router_ips = ', '.join([ router_port_fixed_ip['ip_address']
        for router_port_fixed_ips in router_all_ports_fixed_ips
        for router_port_fixed_ip in router_port_fixed_ips ])
    print ('{} {} (project: {})'.format(router['name'], router_ips, getattr(project, 'name', None)))

