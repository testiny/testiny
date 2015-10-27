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

"""Test fixtures."""

from __future__ import (
    absolute_import,
    print_function,
    unicode_literals,
    )

str = None

__metaclass__ = type
__all__ = []

import keystoneclient
from testiny.config import CONF
from testiny.testcase import TestinyTestCase
from testiny.fixtures.project import ProjectFixture
from testiny.fixtures.user import UserFixture


class TestFixtures(TestinyTestCase):

    def test_create_project(self):
        # TODO: create a test decorator that does this try/except for you.
        try:
            project_fixture = self.useFixture(ProjectFixture())
        except keystoneclient.exceptions.ClientException as e:
            self.fail(e)

        client = self.get_keystone_v3_client_admin(
            project_name=CONF.admin_project)
        projects = [p.name for p in client.projects.list()]
        self.assertIn(project_fixture.name, projects)

    def test_create_user(self):
        # TODO: create a test decorator that does this try/except for you.
        try:
            user_fixture = self.useFixture(UserFixture())
        except keystoneclient.exceptions.ClientException as e:
            self.fail(e)

        client = self.get_keystone_v3_client_admin(
            project_name=CONF.admin_project)
        users = [p.name for p in client.users.list()]
        self.assertIn(user_fixture.name, users)
