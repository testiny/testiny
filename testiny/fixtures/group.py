# Copyright (C) 2016 Julian Edwards
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

"""A fixture that creates a group in Openstack."""

from __future__ import (
    absolute_import,
    print_function,
    unicode_literals,
    )

str = None

__metaclass__ = type
__all__ = [
    "GroupFixture",
    ]

import fixtures
from testiny.clients import get_keystone_v3_client
from testiny.config import CONF
from testiny.factory import factory
from testiny.fixtures import DomainFixture
from testtools.content import text_content


class GroupFixture(fixtures.Fixture):
    """Test fixture that creates a randomly-named group.

    The name is available as the 'name' property after creation.
    """
    def __init__(self, domain=None):
        if domain is not None:
            if isinstance(domain, DomainFixture):
                domain = domain.domain
        self.domain = domain

    def _setUp(self):
        super(GroupFixture, self)._setUp()
        self.name = factory.make_string("testiny")
        self.keystone = get_keystone_v3_client(project_name=CONF.admin_project)
        self.group = self.keystone.groups.create(
            name=self.name, domain=self.domain)
        self.addDetail(
            'GroupFixture', text_content('Group %s created' % self.name))
        self.addCleanup(self.delete)
        return self.user

    def delete(self):
        self.keystone.groups.delete(self.group)
