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

"""Configuration loading and parsing.

Makes available a CONF object at the module level.
"""

from __future__ import (
    absolute_import,
    print_function,
    unicode_literals,
    )

str = None

__metaclass__ = type
__all__ = [
    'CONF'
    ]

import yaml


DEFAULT_CONFIG_FILE = "/etc/testiny/testiny.conf"


def config_to_yaml(filename):
    """Try to return a yaml object from the config at filename.

    If the file doesn't exist, return None. All other exceptions not caught.
    """
    try:
        with open(filename) as conf_file:
            return yaml.safe_load(conf_file)
    except IOError:
        return None


# Look in the current dir for testiny.conf and fall back to
# /etc/testiny/
conf = config_to_yaml("testiny.conf")
if conf is None:
    conf = config_to_yaml(DEFAULT_CONFIG_FILE)


class AttrDict(dict):
    """A dict that allows getattr to work like getitem"""
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


CONF = AttrDict(conf['testiny'])


# TODO: Cache config and make thread safe.
# Might also want a Schema for it but not necessary.
