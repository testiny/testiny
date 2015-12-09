Testiny is a continuous integration test suite that drives Openstack. It is
currently under heavy development.

Its main aims are to run in in a continuous loop on dedicated test
infrastructure, although manual runs are not precluded.

It uses Openstack APIs to drive aspects of Openstack under test, and
requires Neutron rather than Nova net.

Quickstart
==========

1. Copy the sample testiny.conf.sample to testiny.conf and edit to match your
Openstack instance's details.

2. Run tox.

  $ tox

That's it!

The first run will take longer as it builds a virtualenv by downloading
some dependencies. Subsequent runs will start much quicker.


Debugging
=========

If something goes wrong, use `tox -e debug` to run the tests single threaded
outside of testr, which allows pdb to be used.

To debug a single test, run `tox -e test my.test.module.etc`

You can also do `tox -e repl` to run ipython under the debug environment.


Motivation
==========

Why add yet another Openstack testing harness you may ask.  Well, there's
two main alternatives that I've found to be rather problematic in various
ways which are not fixable in the short term.  I won't go into detail here but
I will set out the main aims of Testiny which should make it obvious:

 * Easy to configure.
 * Lightweight; a simple harness using well-established
   Python tooling (Testtools and Fixtures) and Openstack client libraries.
 * Easy to write new tests.
 * Strict test isolation.
 * Clean up well after itself.
 * Can be used for continuous operation, or one-off runs.
 * Can elegantly handle operations outside of the Openstack API, such as
   HA testing.
 * Distinguish configuration and environment problems from actual test
   failures.

Not all of these things are implemented yet but the basics are in place;
you can bring up isolated instances and floating IPs and ping between
instances.

Testiny is opnionated about how it tests. This approach won't be for everyone
but it will work well if you like it.


Testing 101
===========

Tests are the one thing you cannot test, therefore they must be highly readable
and obvious what they are doing.  Testing should follow a simple formula:

 * Set up
 * Apply inputs
 * Perfom action
 * Examine results

Hidden inputs are an anti-pattern, and will not ever happen in Testiny, unlike
some other testing harnesses.

When tests fail, they should also present the developer with *tasteful*
debug information. For example, if something returned an unexpected code,
seeing a traceback in the failure output is nothing but noise.  A good failure
should show what fixtures were set up, what action was being performed at the
time of the failure, and what values didn't match expectations.

In Testiny's case, it will also try very hard to distinguish configuration
and environment failures from actual test failures.


Next
====

There's a bunch of stuff left to do. In no particular order:

 * Add more fixtures for other aspects of Openstack, such as Cinder.
 * Allow pre-configuration of networks instead of creating on the fly.
   (some setups contain networking restrictions that make it hard to do it
   on the fly)
 * Moar tests!
 * Refactor stuff
 * Separate Testiny's own tests from actual target tests.
 * Show better errors than insane tracebacks when something goes wrong.
   The client libraries all return exceptions when a status other than 200
   is returned and these need to be shown as simple errors. Tracebacks imply
   coding errors.
 * Improve fixtures to move through different states more nicely.
