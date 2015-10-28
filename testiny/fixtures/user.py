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

"""A fixture that creates a user in Openstack."""

from __future__ import (
    absolute_import,
    print_function,
    unicode_literals,
    )

str = None

__metaclass__ = type
__all__ = []

import fixtures
from testiny.clients import get_keystone_v3_client
from testiny.config import CONF
from testiny.factory import factory
from testtools.content import text_content


class UserFixture(fixtures.Fixture):
    """Test fixture that creates a randomly-named user.

    The name is available as the 'name' property after creation.
    """
    def setUp(self):
        super(UserFixture, self).setUp()
        self.name = factory.make_string("testiny")
        self.keystone = get_keystone_v3_client(project_name=CONF.admin_project)
        self.password = factory.make_string("password")
        self.user = self.keystone.users.create(
            name=self.name, password=self.password)
        self.addDetail(
            'UserFixture', text_content('User %s created' % self.name))
        self.addCleanup(self.delete_user)
        return self.user

    def delete_user(self):
        self.keystone.users.delete(user=self.user)
