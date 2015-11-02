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

"""A fixture that creates a project in Openstack."""

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
from testiny.fixtures.user import UserFixture
from testtools.content import text_content


class ProjectFixture(fixtures.Fixture):
    """Test fixture that creates a randomly-named project.

    The name is available as the 'name' property after creation.
    The global admin user is automatically added as an admin of the project.
    """
    def setUp(self):
        super(ProjectFixture, self).setUp()
        self.name = factory.make_string("testiny")
        self.keystone = get_keystone_v3_client(project_name=CONF.admin_project)
        self.project = self.keystone.projects.create(
            name=self.name, domain='default')
        self.addDetail(
            'ProjectFixture', text_content('Project %s created' % self.name))
        self.addCleanup(self.delete_project)

        # Automatically give the admin user an admin role on this
        # project.
        self.keystone_admin = get_keystone_v3_client(
            project_name=CONF.admin_project)
        self.admin_user = self.keystone_admin.users.find(name="admin")
        self.add_user_to_role(self.admin_user, "admin")

        return self.project

    def delete_project(self):
        """Delete this project."""
        self.keystone.projects.delete(project=self.project)

    def add_user_to_role(self, user_or_user_fixture, role_name):
        """Give an existing user a role on this project.

        :param user_or_user_fixture: The user, or a userFixture.
        :param role_name: String name of the role (e.g. Member)
        """
        if isinstance(user_or_user_fixture, UserFixture):
            user = user_or_user_fixture.user
        else:
            user = user_or_user_fixture
        keystone = get_keystone_v3_client(project_name=CONF.admin_project)
        role = keystone.roles.find(name=role_name)
        keystone.roles.grant(
            role, user=user, project=self.project)
