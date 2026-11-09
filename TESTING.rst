============
Testing Zuul
============
------------
A Quickstart
------------

This is designed to be enough information for you to run your first tests on
an Ubuntu 20.04 (or later) host.

*Install pip*::

  sudo apt-get install python3-pip

More information on pip here: http://www.pip-installer.org/en/latest/

*Use pip to install nox*::

  pip install nox

A running zookeeper is required to execute tests, but it also needs to be
configured for TLS and a certificate authority set up to handle socket
authentication. Because of these complexities, it's recommended to use a
helper script to set up these dependencies, as well as a database servers::

  sudo apt-get install docker-compose  # or podman-compose if preferred
  ROOTCMD=sudo tools/test-setup-docker.sh

.. note:: Installing and bulding javascript is not required, but tests that
          depend on the javascript assets having been built will be skipped
          if you don't.

*Install javascript tools*::

  tools/install-js-tools.sh

*Install javascript dependencies*::

  pushd web
  yarn install
  popd

*Build javascript assets*::

  pushd web
  yarn build
  popd

Run The Tests
-------------

*Navigate to the project's root directory and execute*::

  nox

Note: completing this command may take a long time (depends on system resources)
also, you might not see any output until nox is complete.

Information about nox can be found here: https://nox.thea.codes/en/stable/


Run The Tests in One Environment
--------------------------------

Nox will run your entire test suite in the sessions specified in the project noxfile.py::

  nox.options.sessions = ["tests-3", "linters"]

To run the test suite in just one of the environments in envlist execute::

  nox -s <env>

so for example, *run the test suite in your default Python interpreter*::

  nox -s tests

or specifically *with Python 3.12*::

  nox -s tests --force-python 3.12

Run One Test
------------

To run individual tests with nox::

  nox -s <env> -- path.to.module.Class.test

For example, to *run a single Zuul test*::

  nox -s tests --force-python 3.12 -- tests.unit.test_scheduler.TestScheduler.test_jobs_executed

To *run one test in the foreground* (after previously having run nox
to set up the virtualenv)::

  .nox/tests/bin/stestr run tests.unit.test_scheduler.TestScheduler.test_jobs_executed

List Failing Tests
------------------

  .nox/tests/bin/activate
  stestr failing --list

Hanging Tests
-------------

The following will run each test in turn and print the name of the
test as it is run::

  . .nox/tests/bin/activate
  stestr run

You can compare the output of that to::

  python -m testtools.run discover --list

Need More Info?
---------------

More information about stestr: http://stestr.readthedocs.io/en/latest/
