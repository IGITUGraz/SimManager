========================
 The Simulation Manager
========================

The Simulation Manager is a library for enabling reproducible scientific simulations. Each time you run your experiment,
the Simulation Manager automatically stores all the metadata required to re-run the simulation with the same exact
version of the code. Additionally, it makes sure that you don't accidentally overwrite your results with multiple runs. 



The Simulation Manager also provides various other miscellaneous utilities (see tools_)

NOTE: This package relies heavily on unix command line tools (e.g. chmod) and
therefore is incompatible with Windows

Installation
============

SimManager requires git to be installed, and your code to be versioned with git.

Currently this package is not available in PyPI. This means that in order to
install the latest version, run::

    pip install https://github.com/IGITUGraz/SimManager/archive/v0.8.3.zip

The installation creates the module `simmanager` from which all the tools in the
package are accesible. It also copies a script file called `subpatch.sh` to the
system path. The details regarding the script are given below

**NOTE:** Make sure the python system path is in ``PATH``. If you're installing the package locally using ``pip install --user``, ``$HOME/.local/bin`` should be in ``PATH``.

How to use
==========
.. code:: python

    import os
    from simmanager import SimManager, Paths


    def simulate_dice_rolls(n_rolls):
        # Placeholder for the actual simulation function
        import random
        return [random.randint(1, 6) for _ in range(n_rolls)]


    def main_sim(output_paths: Paths):
        n_rolls = 1000
        rolls = simulate_dice_rolls(n_rolls)
        # Save the simulation data using output_paths
        with open(output_paths.simulation_path / "dice_rolls.txt", "w") as f:
            f.write("\n".join(map(str, rolls)))


    def analysis_sim(output_paths: Paths):
        # Read the simulation data
        with open(output_paths.simulation_path / "dice_rolls.txt", "r") as f:
            rolls = [int(line.strip()) for line in f.readlines()]

        # Calculate the average roll
        avg_roll = sum(rolls) / len(rolls)

        # Analysis section
        try:
            with open(output_paths.simulation_path / "analysis.txt", "w") as f:
                f.write("This should fail.")
        except PermissionError:
            print("Cannot write to the simulation directory. It's write-protected after the simulation.")

        # Save analysis results to the results directory
        with open(output_paths.results_path / "analysis.txt", "w") as f:
            f.write(f"Average roll: {avg_roll:.2f}")


    if __name__ == "__main__":
        SimName = "DiceSimulation"
        root_dir = os.environ.get("RESULTS_ROOT_DIR")

        if not root_dir:
            raise ValueError("RESULTS_ROOT_DIR environment variable must be set and non-empty")

        with SimManager(SimName, root_dir) as simman:
            main_sim(simman.paths)

        # Initialize a new Paths object with the output path from simman.paths
        new_paths = Paths(simman.paths.output_dir_path)

        #---------------------------
        # Analysis portion
        #---------------------------

        analysis_sim(new_paths)

.. _tools:

Included Tools
==============

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

checkoutsim.sh
++++++++++++++

This script can be used to checkout a particular simulation. usage of the script is
as follows::

    checkoutsim.sh /simulation/output/directory

This script must be run from the directory which is inside the repository containing
the code for the simulation being checked out. For more help type ``checkoutsim.sh``
without any arguments

