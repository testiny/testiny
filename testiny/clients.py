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

"""Openstack API clients for Testiny.

Clients are pre-authenticated using the configuration details.
"""

from __future__ import (
    absolute_import,
    print_function,
    unicode_literals,
    )

str = None

__metaclass__ = type
__all__ = [
    'get_keystone_v3_client',
    'get_nova_v3_client',
    ]

from keystoneclient.auth import identity
from keystoneclient import v3 as keystone_v3
from keystoneclient import session
from neutronclient.neutron import client as neutron_client
from novaclient import client as nova_client
from testiny.config import CONF


# Cached session info.
sessions = dict()


def get_or_create_session(user_name=None, project_name=None,
                          user_domain_name='default',
                          project_domain_name='default', password=None,
                          force_new=False):
    """Return a keystoneclient.session.Session object.

    Sessions are cached on a per (user, project) basis.  If a cached one
    exists, return it, otherwise create a new one.  Setting force_new to
    True always makes a new one.

    If user_name is not set, defaults to the configured admin user.
    If project_name is not set, an unscoped session is created.
    If password is not set, CONF.password is used.
    """
    global sessions

    if user_name is None:
        user_name = CONF.username
    if password is None:
        password = CONF.password
    session_key = (user_name, project_name)
    sess = sessions.get(session_key)
    if sess is not None and force_new is False:
        return sess
    auth = identity.v3.Password(
        CONF.auth_url, username=user_name, password=password,
        project_name=project_name, user_domain_name=user_domain_name,
        project_domain_name=project_domain_name)
    sess = session.Session(auth=auth)
    sessions[session_key] = sess
    return sess


# TODO: Allow client libraries to work out api versionings and remove
# hard-coded versions from here where possible.

def get_keystone_v3_client(user_name=None, project_name=None,
                           user_domain_name='default',
                           project_domain_name='default', password=None):
    sess = get_or_create_session(
        user_name=user_name, project_name=project_name,
        user_domain_name=user_domain_name,
        project_domain_name=project_domain_name, password=password)
    return keystone_v3.Client(version='v3', session=sess)


def get_nova_v3_client(user_name=None, project_name=None,
                       user_domain_name='default',
                       project_domain_name='default', password=None):
    sess = get_or_create_session(
        user_name=user_name, project_name=project_name,
        user_domain_name=user_domain_name,
        project_domain_name=project_domain_name, password=password)
    # TODO: Ensure novaclient v3 available (liberty)
    return nova_client.Client(version='2', session=sess)


def get_neutron_client(user_name=None, project_name=None,
                       user_domain_name='default',
                       project_domain_name='default', password=None):
    sess = get_or_create_session(
        user_name=user_name, project_name=project_name,
        user_domain_name=user_domain_name,
        project_domain_name=project_domain_name, password=password)
    return neutron_client.Client(api_version='2.0', session=sess)
