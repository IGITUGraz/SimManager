import os
from collections import OrderedDict

import re

from sim_manager import SimDataManager, SimDataManagerError

__author__ = 'anand'


class PathsLibraryError(Exception):
    pass


class Paths:
    """
    This is the class that is used to manage the directories involved in the storage of
    simulation output.

    The essence of the path management scheme used by the Paths library lies in the
    concept of an output directory. The output directory is the directory into
    which all the output from the current simulation should go.

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

    The Paths class can be instantiated in one of 2 ways

    1.  Via the `Paths.create_new()` function.
        e.g. ``paths = Paths.create_new(...)``

    2.  Via the `Paths.from_existing()` function
        e.g. ``paths = Paths.from_existing(...)``

    Using the __init__ function (i.e. ``paths = Paths(...)``) is identical to using
    `Paths.create_new()`. See the documentation of the above functions for further
    details regarding the Paths instances created in that way.
    """

    def __init__(self, root_dir_name, root_dir_parent, source_dir='.', suffix="", param_dict={}):
        self.__dict__ = Paths.create_new(root_dir_name=root_dir_name,
                                         root_dir_parent=root_dir_parent,
                                         suffix=suffix,
                                         param_dict=param_dict).__dict__.copy()

    @classmethod
    def from_existing(cls, output_dir_path, suffix=""):
        """
        This returns a Paths object whose `output_dir_path` is assigned to the
        parameter `output_dir_path`.
        """
        self = cls.__new__()
        if not os.path.isdir(output_dir_path):
            raise PathsLibraryError('The path {} passed to Paths.from_existing() does not exist'
                                    .format(output_dir_path))
        self._output_dir_path = output_dir_path
        self._suffix = suffix
        self._from_existing = True
        return self

    @classmethod
    def create_new(cls, root_dir_name, root_dir_parent, source_dir='.', suffix="", param_dict={}):
        """
        This creates a new output directory specified by the parameters above and
        creates a Paths instance associated with it. It also creates all the
        information responsible to reproduce the current simulation and stores it in
        the directory. (look at :meth:`~simplesimman.SimDataManager.create_simulation_data`
        for more details). To see how the output directory is calculated, look at the
        documentation of the `Paths.output_dir_path` property.

        :param root_dir_name: Name of the root directory
        :param root_dir_parent: The directory within which the root directory is created.
        :param source_dir: This should be a directory that is a subdirectory of the
            source repository. By default it takes the value of the current working
            directory.
        :param param_dict: Dictionary in the form of dict(paramname1=param1val, paramname2=param2val).
            See :meth:`Paths.output_dir_path` for where this is used. Default is empty
        :param suffix: Suffix used for various output files

        A paths object vreated using create_new is to be used to store simulation
        results in the simulation, data, and logs subdirectories
        """
        self = cls.__new__()
        self._from_existing = False
        self._root_dir_name = root_dir_name
        self._root_dir_path = root_dir_parent
        if not os.path.exists(root_dir_parent):
            raise PathsLibraryError("{} does not exist. Please create it.".format(root_dir_parent))
        self._suffix = suffix
        self._param_combo = order_dict_alphabetically(param_dict)

        self._aquire_output_dir()
        try:
            self._store_sim_reproduction_data()
        except SimDataManagerError as E:
            os.rmdir(self._output_dir_path)
            raise

        return self

    def _aquire_output_dir(self):
        """
        Create a new output directory for the first time and store simulation data
        in it. If directory already exists, raise a :class:`PathsLibraryError`
        complaining about this.
        """
        self._output_dir_path = self.output_dir_path
        try:
            os.makedirs(self._output_dir_path)
        except OSError:
            raise PathsLibraryError("It appears that the output directory {} already exists."
                                    "Therefore It cannot be created".format(self._output_dir_path))

    def _store_sim_reproduction_data(self, source_repo_dir='.'):
        """
        Stores the relevant simulation data into the data directory

        :param source_repo_dir: The diff is taken of the repository containing the source_repo_dir

        May Raise a SimDataManagerError if the creation of data fails
        """
        sim_man = SimDataManager(source_repo_path=source_repo_dir, output_dir_path=self._output_dir_path)
        sim_man.create_simulation_data()

    @property
    def root_dir_path(self):
        """
        Get the path of the directory containing the output directory
        :return:
        """
        if self._from_existing:
            return os.path.dirname(self._output_dir_path)
        else:
            return os.path.join(self._root_dir_path, self._root_dir_name)

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
        /root_dir_path/root_dir_name/param1name-param1val-param2name-param2val/results/{name}-{param-paramval*}-{kwarg-kwargval*}.ext
        :return:
        """
        param_string = make_param_string(**kwargs)
        return os.path.join(self.results_path, "{}-{}-{}.{}".format(name, param_string, self._suffix, ext))


def make_param_string(delimiter='-', **kwargs):
    """
    Takes a dictionary and constructs a string of the form key1-val1-key2-val2-... (denoted here as {key-val*})
    The keys are alphabetically sorted
    :param str delimiter: Delimiter to use (default is '-')
    :param dict kwargs: A python dictionary
    :return:
    """
    param_string = ""
    for key in sorted(kwargs):
        param_string += delimiter
        param_string += key
        val = kwargs[key]
        if isinstance(val, float):
            param_string += "{}{:.2f}".format(delimiter, val)
        else:
            param_string += "{}{}".format(delimiter, val)
    param_string = re.sub("^-", "", param_string)
    if param_string == "":
        param_string = "default-output-dir"
    return param_string


def order_dict_alphabetically(d):
    """
    Sort a given dictionary alphabetically
    :param dict d:
    :return:
    """
    od = OrderedDict()
    for key in sorted(list(d.keys())):
        assert key not in od
        od[key] = d[key]
    return od
