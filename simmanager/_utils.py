import os
from subprocess import Popen, PIPE
from collections import OrderedDict
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


def make_param_string(delimiter='-', **kwargs):
    """
    Takes a dictionary and constructs a string of the form key1-val1-key2-val2-... (denoted here as {key-val*})
    The keys are alphabetically sorted
    :param str delimiter: Delimiter to use (default is '-')
    :param dict kwargs: A python dictionary
    :return:
    """
    string_list = []
    for key, value in sorted(kwargs.items()):
        string_list.append(key)
        if isinstance(value, float):
            value_string = "{:.2f}".format(value)
        else:
            value_string = "{}".format(value)
        string_list.append(value_string)
    param_string = delimiter.join(string_list)
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


def _rm_anything_recursive(path):
    if not os.path.isdir(path):
        os.remove(path)
    else:
        rmtree(path)
