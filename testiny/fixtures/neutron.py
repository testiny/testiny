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
# Author(s): Julian Edwards

"""A fixture that creates a neutron network in Openstack."""

from __future__ import (
    absolute_import,
    print_function,
    unicode_literals,
    )

str = None

__metaclass__ = type
__all__ = []

import random

import fixtures
from testiny.clients import get_neutron_client
from testiny.config import CONF
from testiny.factory import factory
from testtools.content import text_content


class NeutronNetworkFixture(fixtures.Fixture):
    """Test fixture that creates a randomly-named neutron network.

    The name is available as the 'name' property after creation.
    """
    def __init__(self, project_fixture):
        super(NeutronNetworkFixture, self).__init__()
        self.project_fixture = project_fixture

    def setUp(self):
        super(NeutronNetworkFixture, self).setUp()
        self.neutron = get_neutron_client(
            project_name=self.project_fixture.name,
            user_name=self.project_fixture.admin_user.name,
            password=self.project_fixture.admin_user_fixture.password)
        subnet = random.randint(11, 255)
        cidr = CONF.network['cidr'].format(subnet=subnet)
        # TODO: handle clashes and retry.
        self.net_name = factory.make_string("network-")
        self.sub_name = factory.make_string("subnet-")
        self.network = self.neutron.create_network(
            {"network": dict(name=self.net_name)})
        network_id = self.network["network"]["id"]
        self.subnet = self.neutron.create_subnet(
            {"subnet": dict(
                name=self.sub_name, network_id=network_id, cidr=cidr,
                ip_version=4)})
        self.addDetail(
            'NeutronNetworkFixture-network',
            text_content('Network %s created' % self.net_name))
        self.addDetail(
            'NeutronNetworkFixture-subnet',
            text_content('Subnet %s created' % self.sub_name))
        self.addCleanup(self.delete_network)

    def delete_network(self):
        self.neutron.delete_subnet(self.subnet["subnet"]["id"])
        self.neutron.delete_network(self.network["network"]["id"])
