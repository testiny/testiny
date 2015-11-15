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

# a neutron_client.Client
logging.basicConfig(level=logging.DEBUG)

pp = pprint.PrettyPrinter(indent=4)
neutron = get_neutron_client()

networks = neutron.list_networks()['networks']
network_ids = [network['id'] for network in networks
   if re.match('network-[a-zA-z0-9]{10}$', network['name']) is not None]
pp.pprint (network_ids)

all_subnets = []
for subnets in [net['subnets'] for net in nets]:
    all_subnets.extend(subnets)
pp.pprint (all_subnets)




