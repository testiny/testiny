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

import keystoneclient
from testiny.testcase import TestinyTestCase
from testiny.fixtures.neutron import NeutronNetworkFixture
from testiny.fixtures.project import ProjectFixture
from testiny.fixtures.server import ServerFixture
from testiny.fixtures.user import UserFixture


class TestDHCPResilience(TestinyTestCase):

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

        # TODO: simplify and refactor all fixtures used here
        # A single fixture that composes the others to produce a
        # project, with a user and a network would be good.
        project_fixture.add_user_to_role(user_fixture, 'Member')

        network_fixture = self.useFixture(
            NeutronNetworkFixture(project_name=project_fixture.name))
        network = network_fixture.network
        server_fixture = self.useFixture(
            ServerFixture(project_fixture, user_fixture, network_fixture))

        ip = server_fixture.get_ip_address(network["network"]["name"], 0)
        self.assertEqual(3, ip.count('.'))

        # TODO: inject a file in server.create() and ssh to the instance
        # to find it.
