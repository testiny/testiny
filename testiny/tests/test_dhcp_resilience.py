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
import six
from testiny.config import CONF
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
        self.wait_for_status(server, "ACTIVE", "ERROR")
        start = datetime.datetime.utcnow()
        finish = start + datetime.timedelta(seconds=seconds)
        while datetime.datetime.utcnow() < finish:
            # TODO.
            # This code should work but does not. Networks never appear
            # despite them showing in the dashboard. No idea why.
            # print("networks: %s" % server.networks)
            if len(server.networks.keys()) > 0:
                break
            time.sleep(1)
            server = server.manager.get(server.id)  # refresh server obj
        if len(server.networks.keys()) == 0:
            return None

        if network is not None:
            ips = server.networks.get(network.label)
            if index is not None:
                return ips[index]
            return ips

        ips = server.networks.keys()[0]
        if index is not None:
            return ips[index]
        return ips

    def wait_for_status(self, server, success_statuses, failure_statuses,
                        timeout=60):
        """Wait until 'timeout' seconds for the required status.

        Raises an exception if the server moves to one of the statuses
        in failure_statuses.
        """
        # Convenience or death! Allow strings in place of iterables.
        if isinstance(success_statuses, six.string_types):
            success_statuses = (success_statuses,)
        if isinstance(failure_statuses, six.string_types):
            failure_statuses = (failure_statuses,)

        # Because of
        # https://launchpad.net/python-novaclient/+bug/1494116 we
        # can't do a simple server.manager.get(server.id)
        try:
            server = server.manager.get(server.id)
        except AttributeError:
            self.fail("server.manager.get() failed again. :(")
            server = server.manager.get(server.id)

        start = datetime.datetime.utcnow()
        finish = start + datetime.timedelta(seconds=timeout)
        while datetime.datetime.utcnow() < finish:
            if server.status in success_statuses:
                return server
            if server.status in failure_statuses:
                raise Exception("Server failed: %s" % server.status)
            time.sleep(1)
            server = server.manager.get(server.id)
        # TODO: Custom exceptions please.
        raise Exception("Timed out waiting for server %s" % server.name)

    def create_nova_network(self, nova, project):
        subnet = random.randint(11, 255)
        cidr = CONF.network['cidr'].format(subnet=subnet)
        # TODO: handle clashes and retry.
        return nova.networks.create(
            cidr=cidr, enable_dhcp=1,
            label=self.factory.make_string("network-"), project_id=project.id)

    def create_neutron_network(self, neutron):
        subnet = random.randint(11, 255)
        cidr = CONF.network['cidr'].format(subnet=subnet)
        # TODO: handle clashes and retry.
        net_name = self.factory.make_string("network-")
        sub_name = self.factory.make_string("subnet-")
        network = neutron.create_network({"network": dict(name=net_name)})
        network_id = network["network"]["id"]
        subnet = neutron.create_subnet(
            {"subnet": dict(
                name=sub_name, network_id=network_id, cidr=cidr, ip_version=4)
            })
        return network, subnet

    def delete_nova_network(self, nova, network):
        nova.networks.disassociate(network)
        network.delete()

    def delete_neutron_network(self, neutron, network, subnet):
        neutron.delete_subnet(subnet["subnet"]["id"])
        neutron.delete_network(network["network"]["id"])

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
        # A single fixture that composes the others to produce a
        # project, with a user and a network would be good.

        keystone_admin = self.get_keystone_v3_client_admin()
        member_role = keystone_admin.roles.find(name="Member")
        admin_role = keystone_admin.roles.find(name="admin")
        admin_user = keystone_admin.users.find(name="admin")

        keystone_admin.roles.grant(
            member_role, user=user_fixture.user,
            project=project_fixture.project)
        keystone_admin.roles.grant(
            admin_role, user=admin_user,
            project=project_fixture.project)

        nova = self.get_nova_v3_client(
            user_name=user_fixture.name, project_name=project_fixture.name,
            password=user_fixture.password)
        neutron_admin = self.get_neutron_client(project_name=project_fixture.name)
        network, subnet = self.create_neutron_network(neutron_admin)
        self.addCleanup(
            self.delete_neutron_network, neutron_admin, network, subnet)

        m1tiny = nova.flavors.find(name=CONF.fast_image['flavor_name'])
        image = nova.images.find(name=CONF.fast_image['image_name'])

        #network = self.create_nova_network(
        #    nova_admin, project=project_fixture.project)
        #self.addCleanup(self.delete_nova_network, nova_admin, network)

        nic = [{"net-id": network["network"]["id"]}]
        name = self.factory.make_string('servername')
        userdata = self.factory.make_string('userdata')
        server = nova.servers.create(
            name, image, m1tiny, userdata=userdata, nics=nic)
        self.addCleanup(nova.servers.delete, server)

        ip = self.get_ip_address(server, network, 0)
        self.assertEqual(3, ip.count('.'))

        # TODO: inject a file in server.create() and ssh to the instance
        # to find it.
