import logging
import sys

from ._utils import _changed_to_temp_dir, _get_output

try:  # py3
    from shlex import quote, split
except ImportError:  # py2
    from pipes import quote, split

logger = logging.getLogger('sim_manager')


class SimMetadataManagerError(Exception):
    pass


class CommandLineError(SimMetadataManagerError):
    pass


class InvalidRepoStateError(SimMetadataManagerError):
    pass


class SimMetadataManager:
    """
    This is a wrapper around the functions responsible for generating and storing
    the data relevant to reproducing a simulation
    """

    def __init__(self, source_repo_path, output_dir_path):
        """
        Create a simulation manager object / context manager.__init__

        :param source_repo_path: This is any path inside the repository
            containing the code for your simulation

        :param output_dir_path: The Top-level directory containing all the output
            of the current simulation. This should be a directory that already
            exists
        """

        self.output_dir_path = output_dir_path

        with _changed_to_temp_dir(source_repo_path):
            stdout_, stderr_ = _get_output(['git', 'rev-parse', '--show-toplevel'])

        if not len(stderr_):
            self.repopath = stdout_[:-1]  # remove trailing newline
        else:
            raise CommandLineError(stderr_)

    def create_simulation_metadata(self):
        """
        This is the most important function. This creates all the relevant data
        required to reproduce the simulation and writes it into 4 files in the
        output directory

        1.  DESCRIPTION.yaml - This file is an empty YAML That contains 4 fields:
            title, reason, result, keywords. These can be used to record any data
            that you wish regarding this particular experiment

        2.  .command - This contains the command that was used to run the current
            simulation. Note that it is conspicuously missing the python executable
            as it is built from the values contained in sys.argv

        3.  .commit_id - This contains the commit ID that is currently checked out
            in the repository

        4.  .patch - This contains the diff of the entire repository. Note that the
            diff is taken using a special script that takes diffs and recursively
            across submodules.
        """

        # Create relevant files
        self.create_simulation_description()
        self.create_command_file()
        self.create_commit_id_file()
        self.create_patch_file()

    def get_command(self):
        """
        Returns the path of the main file. This assumes that The simmanager is
        defined in the main file of the simulation
        """
        command_args_list = []

        for arg in sys.argv:
            command_args_list.append(quote(arg))

        return ' '.join(command_args_list)

    def get_commit_id(self):
        with _changed_to_temp_dir(self.repopath):
            stdout_, stderr_ = _get_output(['git', 'rev-parse', 'HEAD'])
            if not len(stderr_):
                return stdout_[:-1]  # remove trailing newline
            else:
                raise CommandLineError(stderr_)

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
                raise CommandLineError(stderr_)

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
                raise CommandLineError(stderr_1.decode('utf-8'))
            if stderr_2:
                raise CommandLineError(stderr_2)
            if stdout_1:
                print("The following files are untracked in submodules:")
                print(stdout_2)
                raise InvalidRepoStateError("The repository submodules contain untracked files. Thus, "
                                            "not take patch as it is likely to miss something I will "
                                            "important that is not tracked.")

            # Check for untracked files in the parent repository
            command_args_list = split("""git status --porcelain""")
            stdout_, stderr_1 = _get_output(command_args_list, as_bytes=True)
            stdout_1, stdout_2 = _get_output(['grep', '-Ee', r'^\?\?'], input_str=stdout_)
            if stderr_1:
                raise CommandLineError(stderr_1.decode('utf-8'))
            if stderr_2:
                raise CommandLineError(stderr_2)
            if stdout_1:
                print("The following files are untracked:")
                print(stdout_1)
                raise InvalidRepoStateError('The repository contains untracked files. Thus, I will'
                                            ' not create patch as it is likely to miss something'
                                            ' that is nor tracked')

    def check_clean(self):
        with _changed_to_temp_dir(self.repopath):
            stdout_, stderr_ = _get_output(['git', 'diff-index', 'HEAD'])

            if not len(stderr_):
                if stdout_:
                    raise InvalidRepoStateError("It appears that the working tree is dirty, "
                                                "Commit/Stash EVERYTHING recursively")
            else:
                raise CommandLineError(stderr_)

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
        yaml_file_string += ["keywords: |"]
        with _changed_to_temp_dir(self.output_dir_path):
            with open('DESCRIPTION.yaml', 'w') as desc_file:
                desc_file.write('\n'.join(yaml_file_string))

    def create_command_file(self):
        with _changed_to_temp_dir(self.output_dir_path):
            with open('.command', 'w') as command_file:
                command_file.write(self.get_command())

    def create_commit_id_file(self):
        with _changed_to_temp_dir(self.output_dir_path):
            with open('.commit_id', 'w') as commit_id_file:
                commit_id_file.write(self.get_commit_id())

    def create_patch_file(self):
        """
        Creates a file storing the diff patch.
        """

        with _changed_to_temp_dir(self.output_dir_path):
            with open('.patch', 'w') as patch_file:
                patch_file.write(self.get_patch())

    def create_lock_file(self):
        """
        Creates a lock file to signify the successful completion of a simulation
        thereby preventing further writes into the same directory
        """
        with _changed_to_temp_dir(self.output_dir_path):
            with open('.sim_manager_write_locked', 'w') as lock_file:
                lock_file.write("THIS FOLDER WILL NOT BE WRITTEN TO BY SIM "
                                "MANAGER DUE TO THE PRESCENCE OF THIS FILE")
