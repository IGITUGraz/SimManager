import os
from collections import OrderedDict

import re

import itertools
from ._utils import _rm_anything_recursive

__author__ = 'anand'

LOCK_FILE_NAME = '.registered_with_paths_library'


class PathsLibraryError(Exception):
    pass


class Paths:

    def __init__(self, root_dir_name, param_dict, suffix="", root_dir_path='./results', create_clean=False):
        """
        Manages generating paths for various cases

        :param root_dir_name: Root dir name where all the subdirectories are created
        :param param_dict: Dictionary in the form of dict(paramname1=param1val, paramname2=param2val).
            See :meth:`Paths.output_dir_path` for where this is used.
        :param suffix: Suffix used for various output files
        :param root_dir_path: The root dir path where the root dir is created
        :param create_clean: The output directory when created is created clean/empty with all previous
            content removed.
        """
        self._root_dir_name = root_dir_name
        self._root_dir_path = root_dir_path
        if not os.path.exists(root_dir_path):
            raise PathsLibraryError("{} does not exit. Please create it.".format(root_dir_path))
        self._suffix = suffix
        self._param_combo = order_dict_alphabetically(param_dict)
        self._create_clean = bool(create_clean)

    def __enter__(self):
        self._as_context_manager = True
        self._create_output_dir_init()

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Here we release our control of the directory by deleting the lock file.
        """
        if exc_type is None:
            self._release_output_dir()
        self._as_context_manager = False

    def _validate_output_directory(self):
        if os.path.isdir(self._output_dir_path):
            if os.path.isfile('.sim_manager_write_locked'):
                raise PathsLibraryError(
                    'The output directory {} already contains a completed simulation'.format(self._output_dir_path))

            if not os.path.isfile(self._lock_file_path):
                raise PathsLibraryError(
                    "It appears that the directory {} already exists and "
                    "is not registered to be overwritten by the Paths library".format(self._output_dir_path))

    def _create_output_dir_init(self):
        """
        Create the output directory for the first time and register it. If directory
        already exists and is not registered as managed by Paths, raise a
        :class:`PathsLibraryError` complaining about this.

        The .sim_manager_locked_file thing is just so that directories created with
        the previous version are not overwritten

        """
        self._output_dir_path = self.output_dir_path
        self._lock_file_path = os.path.join(self._output_dir_path, LOCK_FILE_NAME)

        self._validate_output_directory()

        if os.path.isdir(self._output_dir_path):
            # Clean the output directory and return if create
            if self._create_clean:
                # Clear any previous content from the directory
                for name in os.listdir(self._output_dir_path):
                    name_path = os.path.join(self._output_dir_path, name)
                    if name_path != self._lock_file_path:
                        _rm_anything_recursive(name_path)
        else:
            os.makedirs(self._output_dir_path)
            with open(self._lock_file_path, 'w') as f_lock:
                f_lock.write("The prescence of this file in the directory allows"
                             " the Paths library to overwrite the directory's contents.")

    def _release_output_dir(self):
        """
        Releases the directory from the control of the paths library by removing the
        lock file.
        """
        os.remove(self._lock_file_path)

    def _validate_as_context_manager(self):
        assert self._as_context_manager, "The Paths class needs to be run as a context manager"

    @property
    def root_dir_path(self):
        """
        Get the full path of the root directory
        :return:
        """
        return os.path.join(self._root_dir_path, self._root_dir_name)

    @property
    def output_dir_path(self):
        """
        Get the path of the "output" directory of the form
        /root_dir_path/root_dir_name/param1name-param1val-param2name-param2val. The
        parameter names are sorted in alphabetical order in the leaf directory
        name.
        
        :return: The output directory. If the output directory has not yet been
            created, then it is created as create_output_dir(exist_ok=False) and
            then returned. This is so that the command is not destructive.
        """

        self._validate_as_context_manager()
        return os.path.join(self.root_dir_path, make_param_string(**self._param_combo))

    # The functions that should actually be used are below
    @property
    def results_path(self):
        """
        Get the path of the results directory of the form
        /root_dir_path/root_dir_name/param1name-param1val-param2name-param2val/results
        :return:
        """
        self._validate_as_context_manager()
        path = os.path.join(self.output_dir_path, "results")
        if not os.path.isdir(path):
            os.mkdir(path)
        return path

    @property
    def log_path(self):
        """
        Get the path of the logging directory, creating it  if necesssary
        """
        self._validate_as_context_manager()
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
        self._validate_as_context_manager()
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
        self._validate_as_context_manager()
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
        self._validate_as_context_manager()
        d = self._param_combo.copy()
        d.update(kwargs)
        return os.path.join(self.results_path, "{}-{}{}.{}".format(name, make_param_string(**d), self._suffix, ext))


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


def dict_product(dicts):
    return (dict(zip(dicts, x)) for x in itertools.product(*dicts.values()))


class PathsMap:

    def __init__(self, param_lists, args_name, n_networks, suffix, root_dir_path='./results'):
        """
        This class manages groups of paths for larger simulations of different parameter combinations since each
        :class:`~ltl.paths.Path` above only manages one parameter combination.
        :param param_lists:
        :param args_name:
        :param n_networks:
        :param suffix:
        """
        self._root_dir_name = args_name
        self._root_dir_path = root_dir_path
        self._suffix = suffix

        param_lists.update(dict(network_num=range(n_networks)))
        self.param_lists = param_lists

        list_dict = dict_product(param_lists)
        self.paths_map = {}
        for param_combo in list_dict:
            key = tuple(order_dict_alphabetically(param_combo).items())
            assert key not in self.paths_map
            self.paths_map[key] = Paths(args_name, param_combo, suffix)

    @property
    def paths_list(self):
        return list(self.paths_map.values())

    def get(self, **kwargs):
        param_combo = kwargs
        key = tuple(order_dict_alphabetically(param_combo).items())
        return self.paths_map[key]

    def filter(self, **kwargs):
        filtered_list = []
        for key, paths in self.paths_map.items():
            params_combo = OrderedDict(key)
            for param_name, param_value in kwargs.items():
                if params_combo[param_name] != param_value:
                    break
            else:
                filtered_list.append(paths)

        return filtered_list

    # Aggregate reults paths
    @property
    def root_dir_path(self):
        return os.path.join(self._root_dir_path, self._root_dir_name)

    @property
    def agg_results_path(self):
        path = os.path.join(self.root_dir_path, "results")
        os.makedirs(path, exist_ok=True)
        return path

    def get_agg_fpath(self, name, param_combo, ext, **kwargs):
        d = param_combo.copy()
        d.update(kwargs)
        return os.path.join(self.agg_results_path, "{}-{}{}.{}"
                            .format(name, make_param_string(**d), self._suffix, ext))
