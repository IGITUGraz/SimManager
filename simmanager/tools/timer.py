from timeit import default_timer as timer


class Timer:
    """
    The instances of this class can be used as context managers which can be used
    to profile sections of the code. An example usage is::

        my_timer = Timer(logger, 'INFO')
        with my_timer("Creating a list of 10000 elements"):
            my_list = []
            for i in range(10000):
                my_list.append(i)

    In the above example we create a timer object `my_timer` associated to the
    logger `logger`. We also specify the log level used to output the profiling
    result (in this case 'INFO'). Then we use the object in the with statement by
    calling it with a string that describes the section of code that is being
    profiled (henceforth called the `section name`).

    The above use causes the following log message output at the specified log
    level at the end of the code block::

        <logger related information> Creating a list of 10000 elements took NTW s

    The message takes the form `<section_name> took <profile_time> s`

    Also, the timer object maintains a **list of profile results**. For every use
    in a with statement, a tuple `(section_name, profile_tim)` is recorded in the
    list. The items in the list are chronologically sorted w.r.t the time of
    finishing of the respective code sections. This enables aggregating profile
    results. This list of tuples is accessable in the member `profile_list`. For
    example, in the above example, ``my_timer.profile_list`` would be a list
    containing a single tuple ``("Creating a list of 10000 elements", NTW)``

    :param logger: This is the python logger object that is used to log the profile
        results. Can be `None` (Default), in which case the profiler will not log any
        messages i.e. The profile results are only stored in profile_list but not
        displayed

    :param log_level: This is used to specify a log level to use when logging the
        messages of the logger
    """

    def __init__(self, logger=None, log_level='DEBUG'):
        assert not isinstance(logger, str)  # Check against mistakes from breaking compatibility with LTL timer
        self.profile_list = []
        self._section_name_stack = []
        self._section_start_stack = []
        self._section_counter = 0
        self._logger = logger
        self._log_level = log_level

    def __call__(self, section_name):
        """
        :param section_name: The name of the section being profiled
        """
        self._called_section_name = section_name
        return self

    def __enter__(self):
        if self._called_section_name is not None:
            section_name = self._called_section_name
        else:
            section_name = "Section {}".format(self._section_counter)
        self._section_name_stack.append(section_name)
        self._section_start_stack.append(timer())
        self._section_counter += 1
        return self

    def __exit__(self, *args):
        section_name = self._section_name_stack.pop()
        start = self._section_start_stack.pop()
        end = timer()
        interval = end - start
        self.profile_list.append((section_name, interval))

        if self._logger is not None:
            self._logger.log(self._log_level, "%s took %.4f s", section_name, interval)
