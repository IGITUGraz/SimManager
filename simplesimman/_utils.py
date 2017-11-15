import os
from subprocess import Popen, PIPE
import contextlib
from shutil import rmtree


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


def _rm_anything_recursive(path):
    if not os.path.isdir(path):
        os.remove(path)
    else:
        rmtree(path)