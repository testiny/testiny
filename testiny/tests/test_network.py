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

from netaddr import (
    IPAddress,
    IPNetwork,
)
from testiny.config import CONF
from testiny.fixtures.neutron import (
    NeutronNetworkFixture,
    SecurityGroupRuleFixture,
)
from testiny.fixtures.project import ProjectFixture
from testiny.fixtures.server import (
    IsolatedServerFixture,
    ServerFixture,
)
from testiny.fixtures.user import UserFixture
from testiny.testcase import TestinyTestCase


class TestPingMachines(TestinyTestCase):

    def allow_icmp_traffic(self, project_fixture):
        # Allow ICMP ingress.
        self.useFixture(SecurityGroupRuleFixture(
            project_fixture, 'default', 'ingress', 'icmp'))

    def test_server_gets_internal_dhcp_address(self):
        # Check that a server comes up with a DHCP address from the
        # subnet it's attached to.

        # Inject a random file into a new instance.
        random_filename = "/tmp/%s" % self.factory.make_string("filename-")
        random_content = self.factory.make_string("content-")
        files = {random_filename: random_content}
        server_fixture = self.useFixture(IsolatedServerFixture(files=files))

        # Check that the instance came up on the expected network.
        network = server_fixture.network_fixture.network
        ip = server_fixture.get_ip_address(network["network"]["name"], 0)
        cidr = server_fixture.network_fixture.subnet['subnet']['cidr']
        self.assertIsNotNone(ip, "Internal IP of server is None")
        self.assertIn(
            IPAddress(ip), IPNetwork(cidr),
            "Internal IP of server is not in the expected subnet")

        # TODO: Abstract away the user name somehow.
        out, err, return_code = server_fixture.run_command(
            "sudo cat %s" % random_filename,
            user_name=CONF.fast_image['user_name'],
            key_file_name=server_fixture.keypair_fixture.private_key_file)
        self.assertEqual(
            0, return_code,
            "Failed to read file on server: (%s)" % ''.join(err))
        self.assertEqual(''.join(out), random_content)

    def test_ping_across_networks(self):
        # Two servers in different networks related by a router can reach one
        # another via ping.

        project_fixture = self.useFixture(ProjectFixture())
        user_fixture = self.useFixture(UserFixture())

        # Create a tenant network/subnet for the second server.
        network2_fixture = self.useFixture(
            NeutronNetworkFixture(project_fixture=project_fixture))

        server_fixture = self.useFixture(IsolatedServerFixture(
            project_fixture=project_fixture,
            user_fixture=user_fixture,
        ))

        self.allow_icmp_traffic(server_fixture.project_fixture)

        # Attach second subnet to existing router.
        server_fixture.router_fixture.add_interface_router(
            network2_fixture.subnet["subnet"]["id"])

        # Create a second server in the second network.
        # TODO: figure out why starting two servers in sequence quickly
        # results in them timing out with 'Error: Failed to launch instance:
        # Please try again later [Error: Virtual Interface creation
        # failed].'.
        time.sleep(10)
        server2_fixture = self.useFixture(
            ServerFixture(
                project_fixture,
                user_fixture,
                network2_fixture))

        # Wait for the second server to get an IP address.
        ip2 = server2_fixture.get_ip_address(
            network2_fixture.network["network"]["name"], 0)

        # Wait for the second server to come up.
        # TODO: Poll on something instead of waiting.
        time.sleep(10)

        # Ping private IP of second server from first server.
        out, err, retcode = server_fixture.run_command(
            command='ping -c 5 -W 2 -q %s' % ip2,
            user_name=CONF.fast_image['user_name'],
            key_file_name=server_fixture.keypair_fixture.private_key_file,
        )
        self.assertEqual(
            0, retcode,
            "Can't ping machine in other network (%s)" % ''.join(err))
