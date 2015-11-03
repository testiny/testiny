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

"""A fixture that creates a server instance in Openstack."""

from __future__ import (
    absolute_import,
    print_function,
    unicode_literals,
    )

str = None

__metaclass__ = type
__all__ = [
    "KeypairFixture",
    "ServerFixture",
    "ServerStatusError",
    "TimeoutError",
    ]

import datetime
import os
import subprocess
import time

import fixtures
import novaclient
import six
from testiny.clients import get_nova_v3_client
from testiny.config import CONF
from testiny.factory import factory
from testtools.content import text_content


class TimeoutError(Exception):
    """Raised when the timeout is exceeded for an ssh call."""


class ServerStatusError(Exception):
    """Raised when a server moves into an error state."""


class ServerFixture(fixtures.Fixture):
    """Test fixture that creates a randomly-named server instance.

    The name is available as the 'name' property after creation.
    """
    def __init__(self, project_fixture, user_fixture, network_fixture,
                 **kwargs):
        super(ServerFixture, self).__init__()
        self.project_fixture = project_fixture
        self.user_fixture = user_fixture
        self.network_fixture = network_fixture
        self.instance_kwargs = kwargs

    def setUp(self):
        super(ServerFixture, self).setUp()
        self.nova = get_nova_v3_client(
            user_name=self.user_fixture.name,
            project_name=self.project_fixture.name,
            password=self.user_fixture.password)
        self.name = factory.make_string('testinyservername-')
        m1tiny = self.nova.flavors.find(name=CONF.fast_image['flavor_name'])
        image = self.nova.images.find(name=CONF.fast_image['image_name'])
        nic = [{"net-id": self.network_fixture.network["network"]["id"]}]

        # TODO: Catch errors and show sensible error messages.
        self.server = self.nova.servers.create(
            self.name, image, m1tiny, nics=nic, **self.instance_kwargs)
        self.addCleanup(self.delete_server)

        self.addDetail(
            'ServerFixture',
            text_content('Server instance named %s created' % self.name))

    def delete_server(self):
        self.nova.servers.delete(self.server)
        while True:
            try:
                server = self.server.manager.get(self.server.id)
            except novaclient.exceptions.NotFound:
                break
            if server is None or server.status != 'ACTIVE':
                break
        self.addDetail(
            'ServerFixture',
            text_content('Server instance named %s deleted' % self.name))

    def get_ip_address(self, network_label=None, index=None, seconds=60):
        """Get a server's IP address.

        Will poll the server for up to `seconds` in case it's still
        starting up.

        If network is not None, get the IP on that network, otherwise the
        first network found.

        If index is None, return all IPs on the network.

        Returns None in both cases if no IP address is found.
        """
        self.wait_for_status("ACTIVE", "ERROR")
        start = datetime.datetime.utcnow()
        finish = start + datetime.timedelta(seconds=seconds)

        # Poll until there is a network attached.
        while datetime.datetime.utcnow() < finish:
            server = self.server.manager.get(self.server.id)
            if len(server.networks.keys()) > 0:
                break
            time.sleep(1)
        if len(server.networks.keys()) == 0:
            return None

        # If the user requested a particular network, return its IP(s)
        if network_label is not None:
            ips = server.networks.get(network_label)
            if index is not None:
                return ips[index]
            return ips

        # Return the first network's IP(s)
        ip_item = server.networks.popitem()
        ips = ip_item[1]
        if index is not None:
            return ips[index]
        return ips

    def wait_for_status(self, success_statuses, failure_statuses,
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

        server = self.server.manager.get(self.server.id)

        start = datetime.datetime.utcnow()
        finish = start + datetime.timedelta(seconds=timeout)
        while datetime.datetime.utcnow() < finish:
            if server.status in success_statuses:
                return server
            if server.status in failure_statuses:
                raise Exception("Server failed: %s" % server.status)
            time.sleep(1)
            server = server.manager.get(server.id)
        raise ServerStatusError(
            "Timed out waiting for server %s" % server.name)

    def run_command(self, command, user_name, key_file_name, timeout=60):
        """Use SSH to run the specified command on this server.

        :param command: The command and its args as a string.
        :param timeout: In seconds, the before before which this command must
            complete, else a fixtures.server.TimeoutError is raised.
        :return: (stdout, stderr, return_code) from the command's process.
            stdout and stderr are a list of lines as returned by readlines().
        """
        ip = self.get_ip_address()
        ssh = subprocess.Popen(
            ["ssh", "-i", key_file_name, "%s@%s" % (user_name, ip), command],
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)

        # Python 3 has a timeout parameter for subprocess, but we want
        # to remain compatible with Python 2 for now.
        start = datetime.datetime.utcnow()
        finish = start + datetime.timedelta(seconds=timeout)
        while datetime.datetime.utcnow() < finish:
            ssh.poll()
            if ssh.returncode is not None:
                return (
                    ssh.stdout.readlines(), ssh.stderr.readlines(),
                    ssh.returncode)

        raise TimeoutError


class KeypairFixture(fixtures.Fixture):
    """Test fixture that creates a random keypair."""

    def __init__(self, project_fixture, user_fixture):
        super(KeypairFixture, self).__init__()
        self.user_fixture = user_fixture
        self.project_fixture = project_fixture

    def setUp(self):
        super(KeypairFixture, self).setUp()
        self.nova = get_nova_v3_client(
            user_name=self.user_fixture.name,
            project_name=self.project_fixture.name,
            password=self.user_fixture.password)
        self.name = factory.make_string('keypair')
        self.keypair = self.nova.keypairs.create(name=self.name)
        self.addCleanup(self.delete_keypair)

        self.addDetail(
            'KeypairFixture',
            text_content('Keypair named %s created' % self.name))

        tempdir = self.useFixture(fixtures.TempDir()).path
        self.private_key_file = os.path.join(tempdir, 'test.rsa')
        with open(self.private_key_file, 'wt') as f:
            f.write(self.keypair.private_key)

        self.addDetail(
            'KeypairFixture-private-key-file',
            text_content(
                'Private key file %s created' % self.private_key_file))

    def get(self):
        """Return the private part of the key pair."""
        return self.nova.keypairs.get(self.keypair.id)

    def delete_keypair(self):
        self.keypair.delete()
