Testiny is a continuous integration test suite. It is currently under heavy development.

Its main aims are to run in in a continuous loop on dedicated test infrastructure,
although manual runs are not precluded.

It uses Openstack APIs to drive aspects of Openstack under test.

Quickstart
==========

1. Copy the sample testiny.conf.sample to testiny.conf and edit to match your
Openstack instance's details.

2. Run tox.

  $ tox

That's it!


Debugging
=========

If something goes wrong, use `tox -e debug` to run the tests single threaded outside
of testr, which allows pdb to be used.

You can also do `tox -e repl` to run ipython under the debug environment.
