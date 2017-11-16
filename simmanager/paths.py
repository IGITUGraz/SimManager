import os

from ._utils import make_param_string

__author__ = 'anand'


class PathsLibraryError(Exception):
    pass


class Paths:
    """
    This is the class that is used to conveniently access the directories involved
    in storing simualtion related data and results.

    The core of Paths library lies in the concept of an output directory. The
    output directory is the directory into which all the output from the current
    simulation should go.

    It can contain the following subdirectories (whose path's and creation are handled
    by the corresponding properties)

    1.  `simulation` - This directory contains the raw data that we deem to be the
                       result of the simulation

    2.  `logs` - This is the data containing the output logs from the simulation

    3.  `data` - This contains any intermediate data files that are repeatedly used
                 over the course of the simulation. Honestly the distinction between
                 the simulation and data directory lies in the eyes of the simulator

    4.  `results` - This directory is not used during the simulation. Rather this is
                    used to hold the results of the analysis of the simulation.

    The Paths class is instantiated with the following parameters

    :param output_dir_path: This is the path of the output directory that Paths
        points to. This should be a directory that already exists.
    :param suffix: This is the string that is appended to any file names that are
        acquired via the function get_fpath.
    """

    def __init__(self, output_dir_path, suffix=""):

        if not os.path.isdir(output_dir_path):
            raise PathsLibraryError('The path {} passed to Paths.from_existing() does not exist'
                                    .format(output_dir_path))
        self._output_dir_path = output_dir_path
        self._suffix = suffix

    @property
    def output_dir_path(self):
        """
        Get the path of the "output" directory of the form
        /root_dir_path/root_dir_name/param1name-param1val-param2name-param2val. The
        parameter names are sorted in alphabetical order in the leaf directory
        name.

        :return: The output directory. Note that no creation of the directory
            happens here. If you intend to create the output directory then call
            initialize_output_dir.
        """
        return self._output_dir_path

    # The functions that should actually be used are below
    @property
    def results_path(self):
        """
        Get the path of the results directory of the form
        /root_dir_path/root_dir_name/param1name-param1val-param2name-param2val/results
        :return:
        """
        path = os.path.join(self.output_dir_path, "results")
        if not os.path.isdir(path):
            os.mkdir(path)
        return path

    @property
    def log_path(self):
        """
        Get the path of the logging directory, creating it  if necesssary
        """
        path = os.path.join(self.output_dir_path, "logs")
        if not os.path.isdir(path):
            os.mkdir(path)
        return path

    @property
    def simulation_path(self):
        """
        Get the path of the simulation directory of the form
        /root_dir_path/root_dir_name/param1name-param1val-param2name-param2val/simulation
        :return:
        """
        path = os.path.join(self.output_dir_path, "simulation")
        if not os.path.isdir(path):
            os.mkdir(path)
        return path

    @property
    def data_path(self):
        """
        Get the path of the data directory of the form
        /root_dir_path/root_dir_name/param1name-param1val-param2name-param2val/data
        :return:
        """
        path = os.path.join(self.output_dir_path, "data")
        if not os.path.isdir(path):
            os.mkdir(path)
        return path

    # General function to generate paths
    def get_fpath(self, name, ext, **kwargs):
        """
        Get the path of an arbitrary file of the form
        /output_dir_path/results/{name}-{param-paramval*}-{kwarg-kwargval*}-{suffix}.ext
        :return:
        """
        param_string = make_param_string(**kwargs)
        return os.path.join(self.results_path, "{}-{}-{}.{}".format(name, param_string, self._suffix, ext))
