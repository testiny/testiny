from setuptools import setup

install_reqs = [
    'python-keystoneclient',
    'python-neutronclient',
    'python-novaclient',
    'pyyaml',
    'testinfra',
]

tests_require = [
    'fixtures',
    'flake8',
    'mock',
    'tempest-lib',
    'testrepository',
    'testtools',
    'testscenarios',
]

setup(
    name="testiny",
    version="0.0.0",
    description="Continuous integration suite for Openstack",
    url="https://github.com/metacloud/testiny",
    author="Cisco",
    license="Apache",
    packages=["testiny"],
    install_requires=install_reqs,
    tests_require=tests_require,
    extras_require={'test': tests_require},
    zip_safe=False,
    )
