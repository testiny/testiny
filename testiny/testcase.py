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

"""Base test case class for Testiny test cases."""

from __future__ import (
    absolute_import,
    print_function,
    unicode_literals,
    )

str = None

__metaclass__ = type
__all__ = [
    'TestinyTestCase',
    ]

import fixtures
import mock
from testiny.clients import (
    get_keystone_v3_client,
    get_neutron_client,
    get_nova_v3_client,
)
from testiny.config import CONF
from testiny.factory import factory
import testtools


class TestinyTestCase(testtools.TestCase):
    """Base test class for all Testiny tests.

    Adds some useful helpers.
    """

    factory = factory

    def patch(self, obj, attribute, value=mock.sentinel.unset):
        """Patch obj.attribute with value, returning a Mock.

        This extends the testtools patch() such that if value is
        unspecified, a new MagicMock is created and patched instead.
        """
        if value is mock.sentinel.unset:
            value = mock.MagickMock()
        super(TestinyTestCase, self).patch(obj, attribute, value)

    def make_dir(self):
        """Create a temporary directory.

        Convenience function around the TempDir fixture.
        """
        return self.useFixture(fixtures.TempDir()).path

    def get_keystone_v3_client_admin(self):
        return get_keystone_v3_client(project_name=CONF.admin_project)

    def get_nova_v3_client_admin(self):
        return get_nova_v3_client(
            user_name=CONF.username, project_name=CONF.admin_project,
            password=CONF.password)

    def get_nova_v3_client(self, user_name=None, project_name=None,
                           password=None):
        return get_nova_v3_client(
            user_name=user_name, project_name=project_name, password=password)

    def get_neutron_client_admin(self):
        return get_neutron_client(
            user_name=CONF.username, project_name=CONF.admin_project,
            password=CONF.password)

    def get_neutron_client(self, *args, **kwargs):
        return get_neutron_client(*args, **kwargs)
