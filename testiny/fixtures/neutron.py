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
        self.name = factory.make_string("router-")
        self.router = self.neutron.create_router(
            {'router': {'name': self.name, 'admin_state_up': True}})

        self.addDetail(
            'RouterFixture-network',
            text_content('Router %s created' % self.name))
        self.addCleanup(self.delete_router)

    def add_interface_router(self, subnet_id):
        self.neutron.add_interface_router(
            self.router["router"]["id"], {'subnet_id': subnet_id})
        self.subnet_ids.append(subnet_id)

    def remove_interface_router(self, subnet_id):
        self.neutron.remove_interface_router(
            self.router["router"]["id"], {'subnet_id': subnet_id})

    def add_gateway_router(self, network_id):
        self.neutron.add_gateway_router(
            self.router["router"]["id"], {'network_id': network_id})

    def remove_gateway_router(self):
        self.neutron.remove_gateway_router(
            self.router["router"]["id"])

    def delete_router(self):
        # Delete interfaces first.
        for subnet_id in self.subnet_ids:
            self.remove_interface_router(subnet_id)
        # Delete gateway.
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
                 protocol):
        super(SecurityGroupRuleFixture, self).__init__()
        self.project_fixture = project_fixture
        self.security_group_name = security_group_name
        self.direction = direction
        self.protocol = protocol

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
                }
            })

        self.addDetail(
            'SecurityGroupRuleFixture-network',
            text_content(
                'Security group rule %s created' % self.security_group_rule))
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
