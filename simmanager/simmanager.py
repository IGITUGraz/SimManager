import os

from simmanager.tools.stdouthandling import stdout_teed
from .simmetadatamanager import SimMetadataManager, SimMetadataManagerError
from .paths import Paths
import subprocess
import shlex
from ._utils import _rm_anything_recursive
from ._utils import _get_output

from ._utils import make_param_string
from ._utils import order_dict_alphabetically

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
        ``<root_dir>/<sim_name>/paramname1-paramvalue1-paramname2-paramvalue2..`` . If
        it is successful then it creates a :class:`~simmanager.paths.Paths` instance
        that uses the above path as the output directory. See the
        :class:`~simmanager.paths.Paths` class for more details. This paths object can
        be accessed via the `paths` property. If it cannot create the directory, it
        raises a SimManagerError.

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
    :param param_dict: Dictionary in the form of ``dict(paramname1=param1val, paramname2=param2val)``.
        See point 1. above to see it's usage in creating the output directory.
        Default is an empty dictionary.
    :param suffix: Suffix used for various output files. This is passed on as an
        argument in the creation of the contained Paths object
    :param write_protect_dirs: Enable/Disable write protecting the directories
    :param tee_stdx_to: Give file name here to tee the output to the provided file name.
        A file with the name specified in this argument is created in the `logs`
        sub-directory and used to tee the output to.
    :param open_desc_for_edit: Boolean flag. if this is true, Python will open the
        simulation description file to type in the description of the experiment
        upon creation of the file. The command used to launch the editor is taken
        from the EDITOR environment variable. It defaults to vim.
    """

    def __init__(self, sim_name, root_dir, param_dict={}, suffix="", write_protect_dirs=True, tee_stdx_to=None, open_desc_for_edit=False):

        self._sim_name = sim_name
        self._root_dir = root_dir
        if not os.path.exists(root_dir):
            raise SimManagerError("The root directory {} does not exist. Please create it.".format(root_dir))
        self._suffix = suffix
        self._param_combo = order_dict_alphabetically(param_dict)
        self._write_protect_dirs = write_protect_dirs
        self.tee_stdx_to = tee_stdx_to
        self.open_desc_for_edit = open_desc_for_edit
        self.stdout_redirected_obj = None

    def __enter__(self):
        output_dir_path = self._aquire_output_dir()
        self._paths = Paths(output_dir_path, suffix=self._suffix)
        try:
            self._store_sim_reproduction_data()
        except SimMetadataManagerError as E:
            _rm_anything_recursive(output_dir_path)
            raise
        try:
            if self.open_desc_for_edit:
                description_file = os.path.join(self.paths.output_dir_path, 'DESCRIPTION.yaml')
                editor = os.environ.get('EDITOR', 'vim')
                subprocess.call(shlex.split(editor) + [description_file])
            if self.tee_stdx_to is not None:
                self.stdout_redirected_obj = stdout_teed(os.path.join(self._paths.log_path, self.tee_stdx_to))
        except Exception:
            _rm_anything_recursive(output_dir_path)
            raise
        if self.stdout_redirected_obj is not None:
            self.stdout_redirected_obj._on_enter()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._write_protect_dirs:
            _get_output(['chmod', '-R', 'a-w', self._paths.data_path])
            _get_output(['chmod', '-R', 'a-w', self._paths.simulation_path])
            _get_output(['chmod', '-R', 'a-w', self._paths.log_path])
        if self.stdout_redirected_obj is not None:
            self.stdout_redirected_obj._on_exit()
        return False

    def _aquire_output_dir(self):
        """
        Create a new output directory for the first time and store simulation data
        in it. If directory already exists, raise a :class:`PathsError`
        complaining about this.
        """
        param_string = make_param_string(**self._param_combo)
        if param_string == "":
            output_dir_path = os.path.join(self._root_dir, self._sim_name)
        else:
            output_dir_path = os.path.join(self._root_dir, self._sim_name, param_string)
        try:
            os.makedirs(output_dir_path)
        except OSError:
            raise SimManagerError("It appears that the output directory {} already exists."
                                  "Therefore It cannot be created".format(output_dir_path))
        return output_dir_path

    def _store_sim_reproduction_data(self, source_repo_dir='.'):
        """
        Stores the relevant simulation data into the data directory

        :param source_repo_dir: The diff is taken of the repository containing the source_repo_dir

        May Raise a SimDataManagerError if the creation of data fails
        """
        sim_metadata_man = SimMetadataManager(source_repo_path=source_repo_dir,
                                              output_dir_path=self._paths.output_dir_path)
        sim_metadata_man.create_simulation_metadata()

    @property
    def paths(self):
        """
        Get the path of the directory containing the output directory
        :return:
        """
        if hasattr(self, '_paths'):
            return self._paths
        else:
            raise SimManagerError("It appears as though the output directory has not"
                                  " been created. This is possibly because the SimManager"
                                  " has not been used as a context manager.")

    @property
    def sim_name(self):
        """
        Get the simulation name. Note that the output directory is
        ``<root_dir>/<sim_name>/paramname1-paramvalue1-paramname2-paramvalue2..``

        :return: The simulation name
        """
        return self._sim_name

    @property
    def root_dir(self):
        """
        Get the path of the root directory in which the results are stored. Note that
        the output directory is
        ``<root_dir>/<sim_name>/paramname1-paramvalue1-paramname2-paramvalue2..``
        :return: The root directory
        """
        return self._root_dir
