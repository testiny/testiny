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

import keystoneclient
from testiny.fixtures.neutron import (
    NeutronNetworkFixture,
    RouterFixture,
    SecurityGroupRuleFixture,
)
from testiny.fixtures.project import ProjectFixture
from testiny.fixtures.server import (
    KeypairFixture,
    ServerFixture,
)
from testiny.fixtures.user import UserFixture
from testiny.testcase import TestinyTestCase
from testiny.utils import get_testinfra_connection


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
        server2_fixture = self.useFixture(
            ServerFixture(project_fixture, user_fixture, network2_fixture))

        # Create router and associate subnet interfaces.
        router_fixture = self.useFixture(RouterFixture(project_fixture))
        router_fixture.add_interface_router(
            network1_fixture.subnet["subnet"]["id"])
        router_fixture.add_interface_router(
            network2_fixture.subnet["subnet"]["id"])

        # Wait for the servers to get an IP address.
        server1_fixture.get_ip_address(
            network1_fixture.network["network"]["name"], 0)

        ip2 = server2_fixture.get_ip_address(
            network2_fixture.network["network"]["name"], 0)

        return
        # TODO: get a floating IP and associate it with server 1.
        ext_ip1 = 'a.routable.ip'
        server1_fixture.server.add_floating_ip(ext_ip1)

        conn = get_testinfra_connection(
            hostname=ext_ip1, username='cirros', password='cubswin:)')
        Command = conn.get_module("Command")
        cmd = Command('ping -c 5 -W 2 -q %s' % ip2)
        self.assertEqual(0, cmd.rc, "Can't ping machine in other network")
