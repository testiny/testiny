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
# Author(s): Raphael Badin

"""Testiny utilities."""

from __future__ import (
    absolute_import,
    print_function,
    unicode_literals,
    )

str = None

__metaclass__ = type
__all__ = [
    "check_network_namespace",
    "list_network_namespaces",
    "retry",
    ]

from functools import wraps
import subprocess
import time


def retry(result_checker, num_attempts=4, delay=1):
    """Retry calling the decorated function.

    :param result_checker: a callable returning True when the passed results
        means the call to the decorated function should be retried
    :param num_attempts: number of times to try before giving up
    :param delay: delay between retries in seconds
    """
    def new_retry(func):
        @wraps(func)
        def func_retry(*args, **kwargs):
            attempts = 0
            while attempts < num_attempts - 1:
                result = func(*args, **kwargs)
                if not result_checker(result):
                    return result
                else:
                    time.sleep(delay)
                    attempts += 1
            return func(*args, **kwargs)

        return func_retry

    return new_retry


def list_network_namespaces():
    """List the network namespaces."""
    ns_list = subprocess.check_output(['sudo', 'ip', 'netns', 'list'])
    return ns_list.split()


def check_network_namespace(netns):
    """Raise an exception if a network namespace doesn't exist."""
    if netns not in list_network_namespaces():
        raise Exception("Namespace %s not in machine namespaces.")
