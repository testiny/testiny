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

"""Test network."""

from __future__ import (
    absolute_import,
    print_function,
    unicode_literals,
    )

str = None

__metaclass__ = type
__all__ = []

import time

import keystoneclient
from testiny.config import CONF
from testiny.fixtures.neutron import (
    NeutronNetworkFixture,
    RouterFixture,
    SecurityGroupRuleFixture,
)
from testiny.fixtures.project import ProjectFixture
from testiny.fixtures.server import (
    FloatingIPFixture,
    KeypairFixture,
    ServerFixture,
)
from testiny.fixtures.user import UserFixture
from testiny.testcase import TestinyTestCase


class TestPingMachines(TestinyTestCase):

    def test_ping_across_networks(self):
        try:
            project_fixture = self.useFixture(ProjectFixture())
        except keystoneclient.exceptions.ClientException as e:
            self.fail(e)

        try:
            user_fixture = self.useFixture(UserFixture())
        except keystoneclient.exceptions.ClientException as e:
            self.fail(e)

        project_fixture.add_user_to_role(user_fixture, 'Member')
        keypair_fixture = self.useFixture(
            KeypairFixture(project_fixture, user_fixture))

        # Allow ICMP egress/ingress.
        self.useFixture(SecurityGroupRuleFixture(
            project_fixture, 'default', 'egress', 'icmp'))
        self.useFixture(SecurityGroupRuleFixture(
            project_fixture, 'default', 'ingress', 'icmp'))

        # Create networks/subnets.
        network1_fixture = self.useFixture(
            NeutronNetworkFixture(project_fixture=project_fixture))
        network2_fixture = self.useFixture(
            NeutronNetworkFixture(project_fixture=project_fixture))

        # Create servers.
        server1_fixture = self.useFixture(
            ServerFixture(
                project_fixture, user_fixture, network1_fixture,
                key_name=keypair_fixture.name))
        # TODO: figure out why starting two servers in sequence quickly
        # results in them timing out with 'Error: Failed to launch instance
        # "name: Please try again later [Error: Virtual Interface creation
        # failed].'.
        time.sleep(10)
        server2_fixture = self.useFixture(
            ServerFixture(project_fixture, user_fixture, network2_fixture))

        # Wait for the servers to get an IP address.
        server1_fixture.get_ip_address(
            network1_fixture.network["network"]["name"], 0)

        ip2 = server2_fixture.get_ip_address(
            network2_fixture.network["network"]["name"], 0)

        # Create router and associate subnet interfaces.
        router_fixture = self.useFixture(RouterFixture(project_fixture))
        router_fixture.add_interface_router(
            network1_fixture.subnet["subnet"]["id"])
        router_fixture.add_interface_router(
            network2_fixture.subnet["subnet"]["id"])
        
        # Set public network as gateway to the router.
        external_network_name = CONF.network['external_network']
        external_network = network1_fixture.neutron.list_networks(
            name=external_network_name)['networks'][0]
        router_fixture.add_gateway_router(external_network['id'])

        # Create floatingIP and associate it with server1.
        floatingip1_fixture = self.useFixture(
            FloatingIPFixture(project_fixture, user_fixture, external_network_name))
        server1_fixture.server.add_floating_ip(floatingip1_fixture.ip)

        # Ping private IP of server2 from server.
        _, _, retcode = server1_fixture.run_command(
            command='ping -c 5 -W 2 -q %s' % ip2,
             user_name=CONF.fast_image['user_name'],
             key_file_name=keypair_fixture.private_key_file,
        )
        self.assertEqual(0, retcode, "Can't ping machine in other network")
