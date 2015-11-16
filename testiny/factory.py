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

"""Helper functions and classes for tests."""

from __future__ import (
    absolute_import,
    print_function,
    unicode_literals,
    )

str = None

__metaclass__ = type
__all__ = [
    'factory',
    'OS_OBJECT_PREFIX',
    ]

try:
    from itertools import imap
except ImportError:
    # Python 3
    imap = map
from itertools import (
    islice,
    repeat,
)
import random
import string

# Prefix used when creating Openstack objects.
OS_OBJECT_PREFIX = 'testiny-'


class Factory:
    """Class that defines helpers that make things for you."""

    random_letters = imap(
        random.choice, repeat(string.ascii_letters + string.digits))

    def make_string(self, prefix="", size=10):
        return prefix + "".join(islice(self.random_letters, size))

    def make_obj_name(self, obj_type=""):
        """Create a random name for an Openstack object.

        This will use a common prefix meant to identify quickly
        all the Openstack objects created by a testiny run.

        :param obj_type: Type of the created object.  This will be
            included in the name as a convenience to quickly identify
            the type of an object based on its name.
        """
        prefix = OS_OBJECT_PREFIX
        if obj_type != "":
            prefix = "%s%s-" % (prefix, obj_type)
        return self.make_string(prefix=prefix)


# Factory is a singleton.
factory = Factory()
