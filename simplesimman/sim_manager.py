from . import Paths
from subprocess import Popen, PIPE
import os
import logging
import sys
from shutil import rmtree

import contextlib

try:  # py3
    from shlex import quote, split
except ImportError:  # py2
    from pipes import quote, split

logger = logging.getLogger('sim_manager')


@contextlib.contextmanager
def _changed_to_temp_dir(dirname):
    curdir = os.getcwd()
    try:
        os.chdir(dirname)
        yield dirname
    finally:
        os.chdir(curdir)


def _get_output(args, input_str=None, as_bytes=False):
    if input_str is not None:
        stdin_arg = PIPE
    else:
        stdin_arg = None
    proc = Popen(args, stdout=PIPE, stderr=PIPE, stdin=stdin_arg)
    stdout_, stderr_ = proc.communicate(input=input_str)
    if not as_bytes:
        return stdout_.decode('utf-8'), stderr_.decode('utf-8')
    else:
        return stdout_, stderr_


class SimManager:
    """
    This is a simulation manaager that performs all the drudgery of copying relevant
    stuff to the results folder so that the results are completely reproducible.
    """

    def __init__(self, root_dir_name, param_dict, root_dir_path, overwrite=False):
        """
        Create a simulation manager object / context manager.__init__

        :param root_dir_name: Root dir name where all the subdirectories are created

        :param param_dict: Dictionary in the form of dict(paramname1=param1val,
            paramname2=param2val). See :meth:`Paths.output_dir_path` for where this
            is used.

        :param root_dir_path: The root dir path where the root dir is created

        :param overwrite: If True, then the contents of the directory will be
            overwritten in case the directory exists. Else, an exception is raised.

        NOTE THAT root_dir_name, param_dict, root_dir_path are arguments passed to
        the Paths class. The corresponding paths object can be accessed through the
        `paths` member variable
        """

        self.paths = Paths(root_dir_name=root_dir_name, param_dict=param_dict, root_dir_path=root_dir_path)
        self._overwrite = overwrite
        stdout_, stderr_ = _get_output(['git', 'rev-parse', '--show-toplevel'])

        print(len(stderr_))
        if not len(stderr_):
            self.repopath = stdout_[:-1]  # remove trailing newline
        else:
            raise RuntimeError(stderr_)

    def __enter__(self):
        """
        Here we call the relevant shell script and store its output

        Perform the following sequence of actions:

        check if the directory doesnt already contain a simulation
        if not, store commit ID and diff and YAML template for a description
        """

        # Check if the given directory is valid
        outdirpath = self.paths.output_dir_path
        with _changed_to_temp_dir(outdirpath):
            if os.path.isfile('.sim_manager_write_locked') and not self._overwrite:
                raise RuntimeError(
                    'The output directory {} already contains a completed simulation'.format(outdirpath))

        # Clear any previous content from the directory
        if os.listdir(outdirpath):
            rmtree(outdirpath)
            outdirpath = self.paths.output_dir_path

        # Create relevant files
        self.create_simulation_description()
        self.create_command_file()
        self.create_commit_id_file()
        self.create_patch_file()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Here we lock the directory by creating a lock file
        """
        if exc_type is None:
            self.create_lock_file()
        else:
            print(exc_type)

    def get_command(self):
        """
        Returns the path of the main file. This assumes that The simmanager is
        defined in the main file of the simulation
        """
        command_args_list = []
        print(sys.argv)

        for arg in sys.argv:
            command_args_list.append(quote(arg))

        return ' '.join(command_args_list)

    def get_commit_id(self):
        with _changed_to_temp_dir(self.repopath):
            stdout_, stderr_ = _get_output(['git', 'rev-parse', 'HEAD'])
            if not len(stderr_):
                return stdout_[:-1]  # remove trailing newline
            else:
                raise RuntimeError(stderr_)

    def get_patch(self):
        """
        This does the relevant drudgery of creating a recursive patch by running a
        shell script
        """
        self.check_no_untracked()
        with _changed_to_temp_dir(self.repopath):
            stdout_, stderr_ = _get_output(['subpatch.sh', 'make'])

            if not len(stderr_):
                return stdout_
            else:
                raise RuntimeError(stderr_)

    def check_no_untracked(self):
        with _changed_to_temp_dir(self.repopath):
            command_args_list = split(
                """git submodule foreach '(git status --porcelain | grep -Ee "^\?\?" | tr -s " " | cut -f2 -d " ")'""")
            stdout_, stderr_1 = _get_output(command_args_list, as_bytes=True)

            # gets list of all untracked files in submodules
            stdout_1, stderr_2 = _get_output(['grep', '-vEe', r'^Entering '], input_str=stdout_)

            # Creates formatted list of untracked files
            stdout_2, _ = _get_output(['perl', '-npe', r's/^Entering (.*)$/In Submodule \1/'],
                                      input_str=stdout_, as_bytes=True)
            stdout_2, _ = _get_output(['perl', '-npe', r's/^(?!In Submodule )(.*)$/    \1/'], input_str=stdout_2)

            if stderr_1:
                raise RuntimeError(stderr_1.decode('utf-8'))
            if stderr_2:
                raise RuntimeError(stderr_2)
            if stdout_1:
                print("The following files are untracked in submodules:")
                print(stdout_2)
                raise RuntimeError("The repository submodules contain untracked files. Thus, "
                                   "not take patch as it is likely to miss something I will "
                                   "important that is not tracked.")

            # Check for untracked files in the parent repository
            command_args_list = split("""git status --porcelain""")
            stdout_, stderr_1 = _get_output(command_args_list, as_bytes=True)
            stdout_1, stdout_2 = _get_output(['grep', '-Ee', r'^\?\?'], input_str=stdout_)
            if stderr_1:
                raise RuntimeError(stderr_1.decode('utf-8'))
            if stderr_2:
                raise RuntimeError(stderr_2)
            if stdout_1:
                raise RuntimeError('The repository contains untracked files. Thus, I will'
                                   ' not create patch as it is likely to miss something'
                                   ' that is nor tracked')

    def check_clean(self):
        with _changed_to_temp_dir(self.repopath):
            stdout_, stderr_ = _get_output(['git', 'diff-index', 'HEAD'])

            if not len(stderr_):
                if stdout_:
                    raise RuntimeError("It appears that the working tree is dirty, "
                                       "Commit/Stash EVERYTHING recursively")
            else:
                raise RuntimeError(stderr_)

    def apply_commit_id(self, commit_id):
        self.check_clean()
        with _changed_to_temp_dir(self.repopath):
            stdout_, stderr_ = _get_output(['git', 'checkout'])
            stdout_, stderr_ = _get_output(['git', 'submodule', 'update', '--recursive'])

    def create_simulation_description(self):
        """
        Creates the following Yaml file
        """
        yaml_file_string = []
        yaml_file_string += ["title: {}".format('')]
        yaml_file_string += ["reason: |"]
        yaml_file_string += ["result: |"]
        with _changed_to_temp_dir(self.paths.output_dir_path):
            with open('DESCRIPTION.yaml', 'w') as desc_file:
                desc_file.write('\n'.join(yaml_file_string))

    def create_command_file(self):
        with _changed_to_temp_dir(self.paths.output_dir_path):
            with open('.command', 'w') as command_file:
                command_file.write(self.get_command())

    def create_commit_id_file(self):
        with _changed_to_temp_dir(self.paths.output_dir_path):
            with open('.commit_id', 'w') as commit_id_file:
                commit_id_file.write(self.get_commit_id())

    def create_patch_file(self):
        """
        Creates a file storing the diff patch.
        """

        with _changed_to_temp_dir(self.paths.output_dir_path):
            with open('.patch', 'w') as patch_file:
                patch_file.write(self.get_patch())

    def create_lock_file(self):
        """
        Creates a lock file to signify the successful completion of a simulation
        thereby preventing further writes into the same directory
        """
        with _changed_to_temp_dir(self.paths.output_dir_path):
            with open('.sim_manager_write_locked', 'w') as lock_file:
                lock_file.write("THIS FOLDER WILL NOT BE WRITTEN TO BY SIM "
                                "MANAGER DUE TO THE PRESCENCE OF THIS FILE")
