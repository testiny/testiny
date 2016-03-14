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

"""A fixture that creates a neutron network in Openstack."""

from __future__ import (
    absolute_import,
    print_function,
    unicode_literals,
    )

str = None

__metaclass__ = type
__all__ = [
    "NeutronNetworkFixture",
    "RouterFixture",
    "SecurityGroupRuleFixture",
    ]

from copy import copy

import fixtures
from testiny.clients import get_neutron_client
from testiny.config import CONF
from testiny.utils import synchronized
from testiny.factory import factory
from testiny.utils import wait_until
from testtools.content import text_content

SUBNET_ID_MIN = 11
SUBNET_ID_MAX = 254


class NeutronNetworkFixture(fixtures.Fixture):
    """Test fixture that creates a randomly-named neutron network.

    The name is available as the 'name' property after creation.
    """
    # A record of the available subnet ids.
    available_subnet_ids = set(
        range(SUBNET_ID_MAX, SUBNET_ID_MIN - 1, -1))

    def __init__(self, project_fixture):
        super(NeutronNetworkFixture, self).__init__()
        self.project_fixture = project_fixture

    @classmethod
    @synchronized
    def get_subnet_id(cls):
        """Get an available subnet id."""
        return cls.available_subnet_ids.pop()

    @classmethod
    @synchronized
    def release_subnet_id(cls, id):
        """Release the given subnet id."""
        cls.available_subnet_ids.add(id)

    def _setUp(self):
        super(NeutronNetworkFixture, self)._setUp()
        self.neutron = get_neutron_client(
            project_name=self.project_fixture.name,
            user_name=self.project_fixture.admin_user.name,
            password=self.project_fixture.admin_user_fixture.password)
        self.subnet_id = self.get_subnet_id()
        cidr = CONF.network['cidr'].format(subnet=self.subnet_id)
        # TODO: handle clashes and retry.
        self.net_name = factory.make_obj_name("network")
        self.sub_name = factory.make_obj_name("subnet")
        self.network = self.neutron.create_network(
            {"network": dict(name=self.net_name)})
        network_id = self.network["network"]["id"]
        self.subnet = self.neutron.create_subnet(
            {"subnet": dict(
                name=self.sub_name, network_id=network_id, cidr=cidr,
                ip_version=4)})
        self.addCleanup(self.delete_network)
        self.addDetail(
            'NeutronNetworkFixture-network',
            text_content('Network %s created' % self.net_name))
        self.addDetail(
            'NeutronNetworkFixture-subnet',
            text_content('Subnet %s created (cidr=%s)' % (
                self.sub_name, cidr)))

    def delete_network(self):
        self.neutron.delete_subnet(self.subnet["subnet"]["id"])
        self.neutron.delete_network(self.network["network"]["id"])
        self.release_subnet_id(self.subnet_id)

    def get_network(self, network_name):
        """Fetch network object given its network name.

        Can be used to return networks other than the fixture's in the
        context of the project, e.g. external networks.

        Returns None if not found.
        """
        networks = self.neutron.list_networks(name=network_name)['networks']
        return networks[0] if len(networks) == 1 else None

    def get_external_gateway_ip(self, subnet_index=0):
        """Return the gateway IP of a subnet in the public network."""
        external_network = self.get_network(CONF.network['external_network'])
        subnets = self.neutron.list_subnets(
            network_id=external_network['id'])['subnets']
        return subnets[subnet_index]['gateway_ip']


class RouterFixture(fixtures.Fixture):
    """Test fixture that creates a randomly-named neutron router.

    The name is available as the 'name' property after creation.
    """
    def __init__(self, project_fixture):
        super(RouterFixture, self).__init__()
        self.project_fixture = project_fixture
        self.subnet_ids = []

    def setUp(self):
        super(RouterFixture, self).setUp()
        self.neutron = get_neutron_client(
            project_name=self.project_fixture.name,
            user_name=self.project_fixture.admin_user.name,
            password=self.project_fixture.admin_user_fixture.password)
        # TODO: handle clashes and retry.
        self.name = factory.make_obj_name("router")
        self.router = self.neutron.create_router(
            {'router': {'name': self.name, 'admin_state_up': True}})
        self.addCleanup(self.delete_router)
        self.addDetail(
            'RouterFixture-network',
            text_content('Router %s created' % self.name))
        self.wait_until_active()

    def wait_until_active(self):
        wait_until(lambda: self.refresh()['router']['status'] == 'ACTIVE')

    def refresh(self):
        """Refresh the self.router object."""
        routers = self.neutron.list_routers(
            id=self.router['router']['id'])
        if len(routers) == 1 and len(routers['routers']) == 1:
            self.router['router'] = routers['routers'][0]
        return self.router

    def add_interface_router(self, subnet_id):
        self.neutron.add_interface_router(
            self.router["router"]["id"], {'subnet_id': subnet_id})
        self.subnet_ids.append(subnet_id)

    def remove_interface_router(self, subnet_id):
        self.neutron.remove_interface_router(
            self.router["router"]["id"], {'subnet_id': subnet_id})
        self.subnet_ids.remove(subnet_id)

    def add_gateway_router(self, network_id):
        self.neutron.add_gateway_router(
            self.router["router"]["id"], {'network_id': network_id})

    def remove_gateway_router(self):
        self.neutron.remove_gateway_router(
            self.router["router"]["id"])

    def delete_router(self):
        # Delete interfaces first.
        # Make a copy of the list since it's amended by
        # remove_interface_router as the IDs become available again.
        for subnet_id in copy(self.subnet_ids):
            self.remove_interface_router(subnet_id)
        # Clear gateway.
        self.remove_gateway_router()
        # Delete router.
        self.neutron.delete_router(self.router["router"]["id"])
        self.addDetail(
            'RouterFixture-network',
            text_content('Router %s deleted' % self.name))


class SecurityGroupRuleFixture(fixtures.Fixture):
    """Test fixture that creates a security group rule.

    This assumes the security group already exists.
    """
    def __init__(self, project_fixture, security_group_name, direction,
                 protocol, port_range_min=None, port_range_max=None):
        super(SecurityGroupRuleFixture, self).__init__()
        self.project_fixture = project_fixture
        self.security_group_name = security_group_name
        self.direction = direction
        self.protocol = protocol
        self.port_range_min = port_range_min
        self.port_range_max = port_range_max

    def setUp(self):
        super(SecurityGroupRuleFixture, self).setUp()
        self.neutron = get_neutron_client(
            project_name=self.project_fixture.name,
            user_name=self.project_fixture.admin_user.name,
            password=self.project_fixture.admin_user_fixture.password)
        self.load_security_group()

        self.security_group_rule = self.neutron.create_security_group_rule(
            {
                'security_group_rule': {
                    'direction': self.direction,
                    'security_group_id': self.security_group['id'],
                    'protocol': self.protocol,
                    'port_range_max': self.port_range_max,
                    'port_range_min': self.port_range_min,
                }
            })

        self.addDetail(
            'SecurityGroupRuleFixture-network',
            text_content(
                'Security group rule %s created' % (
                    self.security_group_rule
                    ['security_group_rule']
                    ['security_group_id'])))
        self.addCleanup(self.delete_security_group_rule)

    def load_security_group(self):
        sec_groups = (
            self.neutron.list_security_groups()['security_groups']
        )
        sec_groups = [
            group
            for group in sec_groups
            if group['tenant_id'] == self.project_fixture.project.id and
            group['name'] == self.security_group_name
        ]
        if len(sec_groups) != 1:
            raise Exception(
                "Can't find security group named '%s'" %
                self.security_group_name)
        self.security_group = sec_groups[0]

    def delete_security_group_rule(self):
        self.neutron.delete_security_group_rule(
            self.security_group_rule['security_group_rule']['id'])
        self.addDetail(
            'SecurityGroupRuleFixture-network',
            text_content(
                'Security group rule %s deleted' %
                self.security_group_rule))
