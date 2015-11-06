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
# Author(s): Julian Edwards, Raphael Badin

"""Testing for network-related operations."""

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
from netaddr import (
    IPAddress,
    IPNetwork,
)
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

    def allow_icmp_traffic(self, project_fixture):
        # Allow ICMP egress/ingress.
        self.useFixture(SecurityGroupRuleFixture(
            project_fixture, 'default', 'egress', 'icmp'))
        self.useFixture(SecurityGroupRuleFixture(
            project_fixture, 'default', 'ingress', 'icmp'))

    def allow_ssh_traffic(self, project_fixture):
        # Allow SSH in.
        self.useFixture(SecurityGroupRuleFixture(
            project_fixture, 'default', 'ingress', 'tcp',
            port_range_min=22, port_range_max=22))

    def test_server_gets_internal_dhcp_address(self):
        # A server comes up with a DHCP address from the subnet it's
        # attached to.

        # TODO: create a test decorator that does this try/except for you.
        try:
            project_fixture = self.useFixture(ProjectFixture())
        except keystoneclient.exceptions.ClientException as e:
            self.fail(e)

        try:
            user_fixture = self.useFixture(UserFixture())
        except keystoneclient.exceptions.ClientException as e:
            self.fail(e)

        # TODO: simplify and refactor all fixtures used here
        # A single fixture that composes the others to produce a
        # project, with a user and a network would be good.
        project_fixture.add_user_to_role(user_fixture, 'Member')

        network_fixture = self.useFixture(
            NeutronNetworkFixture(project_fixture=project_fixture))

        self.allow_icmp_traffic(project_fixture)
        self.allow_ssh_traffic(project_fixture)

        # Create a keypair.
        keypair_fixture = self.useFixture(
            KeypairFixture(project_fixture, user_fixture))

        # Inject a random file into a new instance.
        random_filename = "/tmp/%s" % self.factory.make_string("filename-")
        random_content = self.factory.make_string("content-")
        files = {random_filename: random_content}
        server_fixture = self.useFixture(
            ServerFixture(project_fixture, user_fixture, network_fixture,
                          key_name=keypair_fixture.name, files=files))

        # Check that the instance came up on the expected network.
        network = network_fixture.network
        ip = server_fixture.get_ip_address(network["network"]["name"], 0)
        cidr = network_fixture.subnet['subnet']['cidr']
        self.assertIsNotNone(ip, "Internal IP of server is None")
        self.assertIn(
            IPAddress(ip), IPNetwork(cidr),
            "Internal IP of server is not in the expected subnet")

        router_fixture = self.useFixture(RouterFixture(project_fixture))
        router_fixture.add_interface_router(
            network_fixture.subnet["subnet"]["id"])

        # Set public network as gateway to the router to allow inbound
        # connections to server1.
        external_network_name = CONF.network['external_network']
        external_network = network_fixture.get_network(external_network_name)
        router_fixture.add_gateway_router(external_network['id'])

        # Create floatingIP and associate it with server.
        floatingip_fixture = self.useFixture(
            FloatingIPFixture(
                project_fixture, user_fixture, external_network_name))
        server_fixture.server.add_floating_ip(floatingip_fixture.ip)

        # TODO: Hide away this key pair management somehow.
        # TODO: Abstract away the user name somehow.
        out, err, return_code = server_fixture.run_command(
            "sudo cat %s" % random_filename,
            user_name=CONF.fast_image['user_name'],
            key_file_name=keypair_fixture.private_key_file)
        self.assertEqual(
            0, return_code,
            "Failed to read file on server: (%s)" % ''.join(err))
        self.assertEqual(''.join(out), random_content)

    def test_ping_across_networks(self):
        # Two servers in different networks related by a router can reach one
        # another via ping.

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

        self.allow_icmp_traffic(project_fixture)
        self.allow_ssh_traffic(project_fixture)

        # Create 2 tenant networks/subnets.
        network1_fixture = self.useFixture(
            NeutronNetworkFixture(project_fixture=project_fixture))
        network2_fixture = self.useFixture(
            NeutronNetworkFixture(project_fixture=project_fixture))

        # Create 2 servers.
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

        # Set public network as gateway to the router to allow inbound
        # connections to server1.
        external_network_name = CONF.network['external_network']
        external_network = network1_fixture.get_network(external_network_name)
        router_fixture.add_gateway_router(external_network['id'])

        # Create floatingIP and associate it with server1.
        floatingip1_fixture = self.useFixture(
            FloatingIPFixture(
                project_fixture, user_fixture, external_network_name))
        server1_fixture.server.add_floating_ip(floatingip1_fixture.ip)

        # Ping private IP of server2 from server.
        _, err, retcode = server1_fixture.run_command(
            command='ping -c 5 -W 2 -q %s' % ip2,
            user_name=CONF.fast_image['user_name'],
            key_file_name=keypair_fixture.private_key_file,
        )
        self.assertEqual(
            0, retcode,
            "Can't ping machine in other network (%s)" % ''.join(err))
