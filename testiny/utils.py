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

"""Utilities."""

import paramiko
import testinfra


def get_testinfra_connection(hostname, username, password):
    """Utility to create a testinfra SSH connection."""
    # This exists to encapsulate the workarounds around testinfra's
    # current limitations
    client = paramiko.SSHClient()
    # Skip host key validation.
    client.set_missing_host_key_policy(paramiko.client.AutoAddPolicy)
    client.connect(hostname=hostname, username=username, password=password)
    conn = testinfra.get_backend("paramiko://%s:22")
    # Put own client in conn because testinfra's API doesn't support
    # password-based logins yet.
    conn._client = client
    return conn
