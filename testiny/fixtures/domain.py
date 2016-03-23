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

"""A fixture that creates a domain in Openstack."""

from __future__ import (
    absolute_import,
    print_function,
    unicode_literals,
    )

str = None

__metaclass__ = type
__all__ = [
    "DomainFixture",
    ]

import fixtures
from testiny.clients import get_keystone_v3_client
from testiny.config import CONF
from testiny.factory import factory
from testtools.content import text_content


class DomainFixture(fixtures.Fixture):
    """Test fixture that creates a randomly-named domain.

    The name is available as the 'name' property after creation.
    """
    def _setUp(self):
        super(DomainFixture, self)._setUp()
        self.name = factory.make_string("testiny")
        self.keystone = get_keystone_v3_client(project_name=CONF.admin_project)
        self.domain = self.keystone.domains.create(name=self.name)
        self.addDetail(
            'DomainFixture', text_content('Domain %s created' % self.name))
        self.addCleanup(self.delete)
        return self.user

    def delete(self):
        self.keystone.domains.update(self.domain, enabled=False)
        self.keystone.domains.delete(self.domain)
