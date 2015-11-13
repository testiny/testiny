#!/usr/bin/env bash

set -o pipefail

if [ ! -e testiny.conf ] && [ ! -e /etc/testiny/testiny.conf ] ; then
    echo "testiny.conf missing, please copy from testiny.conf.example and edit to match your local Openstack installation"
    exit 1
fi

TESTRARGS=$1
python setup.py testr --testr-args="--subunit $TESTRARGS" | subunit-trace -f
retval=$?
echo -e "\nSlowest Tests:\n"
testr slowest
exit $retval

