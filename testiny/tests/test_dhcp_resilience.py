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

"""Test DHCP resilience."""

from __future__ import (
    absolute_import,
    print_function,
    unicode_literals,
    )

str = None

__metaclass__ = type
__all__ = []

import datetime
import random
import time

import keystoneclient
from testiny.testcase import TestinyTestCase
from testiny.fixtures.project import ProjectFixture
from testiny.fixtures.user import UserFixture


class TestDHCPResilience(TestinyTestCase):

    # TODO refactor all of these helpers somewhere else, and/or make it
    # much easier to start an instance in a test case based on its
    # fixtures.

    def get_ip_address(self, server, network=None, index=None, seconds=60):
        """Get a server's IP address.

        Will poll the server for up to `seconds` in case it's still
        starting up.

        If network is not None, get the IP on that network, otherwise the
        first network found.

        If index is None, return all IPs on the network.


        Returns None in both cases if no IP address is found.
        """
        start = datetime.datetime.utcnow()
        finish = start + datetime.timedelta(seconds=seconds)
        while datetime.datetime.utcnow() < finish:
            server.manager.get(server.id)  # refresh server obj
            # TODO.
            # This code should work but does not. Networks never appear
            # despite them showing in the dashboard. No idea why.
            # print("networks: %s" % server.networks)
            if len(server.networks.keys()) > 0:
                break
            time.sleep(1)
        if len(server.networks.keys()) == 0:
            return None

        if network is not None:
            ips = server.networks.get(network)
            if index is not None:
                return ips[index]
            return ips

        ips = server.networks.keys()[0]
        if index is not None:
            return ips[index]
        return ips

    def create_nova_network(self, nova, project):
        # TODO: make network CIDR configurable
        subnet = random.randint(11,255)
        cidr = "10.0.{subnet}.0/24".format(subnet=subnet)
        return nova.networks.create(
            cidr=cidr, enable_dhcp=1, label=self.factory.make_string("network"),
            project_id=project.id)

    def delete_nova_network(self, nova, network):
        nova.networks.disassociate(network)
        network.delete()

    def test_server_gets_dhcp_address(self):
        # TODO: create a test decorator that does this try/except for you.
        try:
            project_fixture = self.useFixture(ProjectFixture())
        except keystoneclient.exceptions.ClientException as e:
            self.fail(e)

        try:
            user_fixture = self.useFixture(UserFixture())
        except keystoneclient.exceptions.ClientException as e:
            self.fail(e)

        # TODO: simplify and refactor all fixtures used below here

        keystone_admin = self.get_keystone_v3_client_admin()
        member_role = keystone_admin.roles.find(name="Member")

        keystone_admin.roles.grant(
            member_role, user=user_fixture.user,
            project=project_fixture.project)

        nova = self.get_nova_v3_client(
            user_name=user_fixture.name, project_name=project_fixture.name,
            password=user_fixture.password)
        nova_admin = self.get_nova_v3_client_admin()

        m1tiny = nova.flavors.find(name="m1.tiny")
        image = nova.images.find(name="cirros-0.3.2-x86_64-uec")

        network = self.create_nova_network(nova_admin, project=project_fixture.project)
        self.addCleanup(self.delete_nova_network, nova_admin, network)

        nic = [{"net-id": network.id}]
        name = self.factory.make_string('servername')
        userdata = self.factory.make_string('userdata')
        server = nova.servers.create(name, image, m1tiny, userdata=userdata, nics=nic)
        self.addCleanup(nova.servers.delete, server)

        ip = self.get_ip_address(server, network, 0)
        self.assertEqual(3, ip.count('.'))

