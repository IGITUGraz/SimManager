import os

from simdatamanager import SimDataManager, SimDataManagerError
from paths import Paths
from _utils import _rm_anything_recursive
from _utils import _get_output

from _utils import make_param_string
from _utils import order_dict_alphabetically

__author__ = 'anand'


class SimManagerError(Exception):
    pass


class SimManager:
    """
    This is the class that is used to manage the directories involved in the storage of
    simulation output. It must be used as a context manager. An example is below::

        with SimManager(sim_name, root_dir) as simman:
            ...
            ...
            # This part contains the relevant code that performs the simulation
            ...

    The simulation manager does the following:

    1.  On entering the context it attempts to create a directory by the name of
        ``<root_dir>/<sim_name>/paramname1-paramvalue1-paramname2-paramvalue2.. .`` If
        it is successful then it creates a :class:`~simmanager.paths.Paths` instance
        that uses the above path as the output directory. See the
        :class:`~simmanager.paths.Paths` class for more details. This paths object can
        be accessed via the `paths` property. If it cannot create the directory, it
        raises an exception

    2.  After creating the directory, the SimManager creates 4 files in the output
        directory that contain all the information necessary to reproduce the
        simulation. For more details look at the documentation of
        :meth:`simmanager.simdatamanager.SimDataManager.create_simulation_data` in the
        :meth:`simmanager.simdatamanager.SimDataManager` class.

    3.  On exit (whether due to exception or not), The simulation manager removes write
        permission from all subdirectories of the output directory EXCEPT the results
        directory (This is because the results directory is intended to be used to
        collect the results of analysis that is conducted after the simulation).

    :param sim_name: Simulation Name
    :param root_dir: Root directory containing results. See point 1. above for more
        details
    :param source_dir: This should be a directory that is a subdirectory of the
        source repository. By default it takes the value of the current working
        directory.
    :param param_dict: Dictionary in the form of ``dict(paramname1=param1val, paramname2=param2val)``.
        See point 1. above to see it's usage in creating the output directory.
        Default is an empty dictionary.
    :param suffix: Suffix used for various output files. This is passed on as an
        argument in the creation of the contained Paths object

    """

    def __init__(self, sim_name, root_dir, source_dir='.', param_dict={}, suffix=""):

        self._sim_name = sim_name
        self._root_dir = root_dir
        if not os.path.exists(root_dir):
            raise SimManagerError("The root directory {} does not exist. Please create it.".format(root_dir))
        self._suffix = suffix
        self._param_combo = order_dict_alphabetically(param_dict)
        self._as_context_manager = False

    def __enter__(self):
        output_dir_path = self._aquire_output_dir()
        self._paths = Paths(output_dir_path, suffix=self._suffix)
        try:
            self._store_sim_reproduction_data()
        except SimDataManagerError as E:
            _rm_anything_recursive(self._output_dir_path)
            raise
        self._as_context_manager = True

    def __exit__(self, exc_type, exc_value, traceback):
        _get_output(['chmod', '-R', 'a-w', self._paths.data_path])
        _get_output(['chmod', '-R', 'a-w', self._paths.simulation_path])
        _get_output(['chmod', '-R', 'a-w', self._paths.log_path])
        self._as_context_manager = False

    def _aquire_output_dir(self):
        """
        Create a new output directory for the first time and store simulation data
        in it. If directory already exists, raise a :class:`PathsError`
        complaining about this.
        """
        output_dir_path = os.path.join(self._root_dir, self._sim_name, make_param_string(**self._param_combo))
        try:
            os.makedirs(output_dir_path)
        except OSError:
            raise SimManagerError("It appears that the output directory {} already exists."
                                  "Therefore It cannot be created".format(self._output_dir_path))
        return output_dir_path

    def _store_sim_reproduction_data(self, source_repo_dir='.'):
        """
        Stores the relevant simulation data into the data directory

        :param source_repo_dir: The diff is taken of the repository containing the source_repo_dir

        May Raise a SimDataManagerError if the creation of data fails
        """
        sim_man = SimDataManager(source_repo_path=source_repo_dir,
                                 output_dir_path=self._paths.output_dir_path)
        sim_man.create_simulation_data()

    @property
    def paths(self):
        """
        Get the path of the directory containing the output directory
        :return:
        """
        return self._paths

    @property
    def sim_name(self):
        """
        Get the path of the directory containing the output directory
        :return:
        """
        return self._sim_name

    @property
    def root_dir(self):
        """
        Get the path of the directory containing the output directory
        :return:
        """
        return self._root_dir
