from pip.req import parse_requirements
from setuptools import setup

install_reqs = parse_requirements("requirements.txt")
test_reqs = parse_requirements("test-requirements.txt")

setup(
    name="testiny",
    version="0.0.0",
    description="Continuous integration suite for Openstack",
    url="https://github.com/metacloud/testiny",
    author="Cisco",
    license="Apache",
    packages=["testiny"],
    install_requires=[str(ir.req) for ir in install_reqs],
    tests_require=[str(ir.req) for ir in test_reqs],
    zip_safe=False,
    )
