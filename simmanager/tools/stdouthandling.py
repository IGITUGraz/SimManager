from contextlib import contextmanager
import os
import sys


@contextmanager
def stdout_redirected(filename):
    """
    This context manager causes all writes to stdout (whether within python or its
    subprocesses) to be redirected to the filename specified. For usage, look at
    example below::

        import os

        with stdout_redirected(filename):
            print("from Python")
            os.system("echo non-Python applications are also supported")

    inspired from the article
    http://eli.thegreenplace.net/2015/redirecting-all-kinds-of-stdout-in-python/

    :param filename: The filename (NOT file stream object, this is to ensure that
        the stream is always a valid file object) to which the stdout is to be
        redirected
    """

    os_stdout_fd = sys.stdout.fileno()
    assert os_stdout_fd == 1, "Doesn't work if stdout is not the actual __stdout__"

    sys.stdout.flush()
    old_stdout = sys.stdout
    old_stdout_fd_dup = os.dup(sys.__stdout__.fileno())

    # # assert that Python and C stdio write using the same file descriptor
    # assert libc.fileno(ctypes.c_void_p.in_dll(libc, "stdout")) == os_stdout_fd == 1

    def _redirect_stdout(filestream):
        os.dup2(filestream.fileno(), os_stdout_fd)  # os_stdout_fd writes to 'to' file
        sys.stdout = os.fdopen(os_stdout_fd, 'w')  # Python writes to os_stdout_fd

    def _revert_stdout():
        sys.stdout.close()
        os.dup2(old_stdout_fd_dup, os_stdout_fd)
        os.close(old_stdout_fd_dup)
        sys.stdout = old_stdout

    with open(filename, 'w') as file:
        _redirect_stdout(filestream=file)
        try:
            yield  # allow code to be run with the redirected stdout
        finally:
            _revert_stdout()


@contextmanager
def stdout_discarded():
    """
    This context manager causes all writes to stdout (whether within python or its
    subprocesses) to be redirected to `os.devnull`, thereby effectively discarding the
    output. For usage look at example below::

        import os

        with stdout_discarded():
            print("from Python")
            os.system("echo non-Python applications are also supported")
    """
    with stdout_redirected(os.devnull):
        yield
