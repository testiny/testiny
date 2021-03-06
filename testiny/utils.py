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
    "parse_ping_output",
    "retry",
    "synchronized",
    "wait_until",
    ]

import datetime
from functools import wraps
import re
import subprocess
import threading
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


def wait_until(predictate, timeout=60, timeout_msg='', delay=0.25):
    """Wait until a predicate is true."""
    start = datetime.datetime.utcnow()
    finish = start + datetime.timedelta(seconds=timeout)
    while datetime.datetime.utcnow() < finish:
        if predictate():
            return
        time.sleep(delay)
    raise Exception("Timed out %s" % timeout_msg)


def list_network_namespaces():
    """List the network namespaces."""
    ns_list = subprocess.check_output(['sudo', 'ip', 'netns', 'list'])
    return ns_list.split()


def check_network_namespace(netns):
    """Raise an exception if a network namespace doesn't exist."""
    if netns not in list_network_namespaces():
        raise Exception("Namespace %s not in machine namespaces.")


def parse_ping_output(ping_output):
    """Parse ping output.

    Returns a tuple with the number of packets sent and the percentage of
    packet loss from a ping output."""
    match = re.search(
        '(\d*) packets transmitted, .* ([\d\.]*)\% packet loss',
        ping_output)
    return match.groups() if match is not None else None


def synchronized(func):
    """Decorator to make a function threadsafe."""
    lock = threading.Lock()

    def wrap(*args, **kwargs):
        lock.acquire()
        try:
            return func(*args, **kwargs)
        finally:
            lock.release()
    return wrap
