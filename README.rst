========================
 The Simulation Manager
========================

This repository contains tools that are useful for manipulating directories,
storing data necessary to reproduce the simulations, profile code and redirect
stdout output (even from system level code).

NOTE: This package relies heavily on unix command line tools (e.g. chmod) and
therefore is incompatible with Windows

Installation
============

Currently this package is not available in PyPI. This means that in order to
install it, clone this repository and run the following command from inside the
repository::

    pip install .

The installation creates the module `simmanager` from which all the tools in the
package are accesible. It also copies a script file called `subpatch.sh` to the
system path. The details regarding the script are given below

Tools Contained
===============

SimManager Class
++++++++++++++++

This class is a context manager that wraps the simulation code. This is responsible
for creating a directory to store simulation results as well as store the data
necessary for the reproduction of simulation results. It also removes write access
to the directories that contain the simulation results when exiting the context.
This is so that the results are never accidentally overwritten. Look at the
documentation of SimManager for more details.

Paths Class
+++++++++++

This class helps in conveniently getting the path names that are involved in the
storing of results. Look at the documentation of the class for more information.

tools.timer.Timer Class
+++++++++++++++++++++++

A useful timer used as a context manager. This measures the wall clock time elapsed
in the execution of a particular context and logs and stores it. Look at the class
documentation for more information.

tools.stdouthandling module
+++++++++++++++++++++++++++

This manager contains code that is used to redirect stdout output. The difference
between this and standard stdout redirection is that this code redirects even
system level output. It contains the functions `stdout_redirected` and
`stdout_discarded`. See function documentation for more details.

Scripts
=======

subpatch.sh
+++++++++++

This script is used to take a diff of the entire repository including submodules
recursively. The script can also be used to patch a repository. The usage of the
script is as follows::

    subpatch.sh make > patch.txt       # To create a patch file
    cat patch.txt | subpatch.sh apply  # To apply a patch file

Note that in order to patch a repository it is necessary that it is checked out to
the commit on which the patch was created. If there are any submodules it is
necessary that they too are checked out to the correct commit id's.
