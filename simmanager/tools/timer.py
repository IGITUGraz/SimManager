from timeit import default_timer as timer
import logging


class Timer:
    """
    The instances of this class can be used as context managers which can be used
    to profile sections of the code. An example usage is::

        from simmanager.tools.timer import Timer
        import logging
        import sys

        logging.basicConfig(stream=sys.stdout, level='DEBUG')
        logger = logging.getLogger('timer_info')

        my_timer = Timer(logger, 'INFO')
        n_elems = 100000
        with my_timer("Creating a list of {} elements".format(n_elems)):
            my_list = []
            for i in range(n_elems):
                my_list.append(i)

    This causes the following output::

        INFO:timer_info:Creating a list of 100000 elements took 0.0150 s

    In the above example we create a timer object `my_timer` associated to the
    logger `logger`. We also specify the log level used to output the profiling
    result (in this case 'INFO'). Then we use the object in the with statement by
    calling it with a string that describes the section of code that is being
    profiled (henceforth called the `section name`). This causes a log message of
    the form `<section_name> took <profile_time> s` to be output at the end of the
    section.

    NOTE: The timer contexts CAN BE NESTED. i.e. the following example is a valid
    use of `my_timer`::

        from simmanager.tools.timer import Timer
        import logging
        import sys

        logging.basicConfig(stream=sys.stdout, level='DEBUG')
        logger = logging.getLogger('timer_info')

        my_timer = Timer(logger, 'INFO')
        n_elems = 100000
        with my_timer("Creating a list of {} elements".format(n_elems)):
            my_list = []
            with my_timer("Adding First {} elements in list".format(n_elems//2)):
                for i in range(n_elems//2):
                    my_list.append(i)
            with my_timer("Adding Second {} elements in list".format(n_elems//2)):
                for i in range(n_elems//2):
                    my_list.append(i)

    This causes the following output::

        INFO:timer_info:Adding First 50000 elements in list took 0.0079 s
        INFO:timer_info:Adding Second 50000 elements in list took 0.0076 s
        INFO:timer_info:Creating a list of 100000 elements took 0.0157 s

    NOTE that the output is in the order of the ending times of the respective contexts

    Also, the timer object maintains a **list of profile results**. For every use
    in a with statement, a tuple `(section_name, profile_tim)` is recorded in the
    list. The items in the list are chronologically sorted w.r.t the time of
    finishing of the respective code sections. This enables aggregating profile
    results. This list of tuples is accessable in the member `profile_list`. For
    example, if we consider the second example above (i.e. nested contexts), the
    value of ``my_timer.profile_list`` is as below::

        [('Adding First 50000 elements in list', 0.007867546984925866),
         ('Adding Second 50000 elements in list', 0.007617355091497302),
         ('Creating a list of 100000 elements', 0.015676741022616625)]


    :param logger: This is the python logger object that is used to log the profile
        results. Can be `None` (Default), in which case the profiler will not log any
        messages (i.e. The profile results are only stored in profile_list but not
        displayed)

    :param log_level: This is used to specify a log level to use when logging the
        messages of the logger
    """

    def __init__(self, logger=None, log_level='DEBUG'):
        assert not isinstance(logger, str)  # Check against mistakes from breaking compatibility with LTL timer
        self.profile_list = []
        self._section_name_stack = []
        self._section_start_stack = []
        self._section_log_level_stack = []
        self._section_counter = 0
        self._logger = logger

        if str(log_level) == log_level:
            self._log_level = logging.getLevelName(log_level)
        elif isinstance(log_level, int):
            self._log_level = log_level

        self._called_section_name = None
        self._called_log_level = self._log_level

    def __call__(self, section_name, log_level=None):
        """
        :param section_name: The name of the section being profiled
        :param log_level: Specifies the log level for the profile message for this
            particular section. overrides the default log level that was set in the
            __init__ function (i.e. constructor).
        """
        self._called_section_name = section_name
        if log_level is None:
            self._called_log_level = self._log_level
        elif str(log_level) == log_level:
            self._called_log_level = logging.getLevelName(log_level)
        elif isinstance(log_level, int):
            self._called_log_level = log_level
        return self

    def __enter__(self):
        if self._called_section_name is not None:
            section_name = self._called_section_name
        else:
            section_name = "Section {}".format(self._section_counter)
        self._section_name_stack.append(section_name)
        self._section_start_stack.append(timer())
        self._section_log_level_stack.append(self._called_log_level)

        self._called_section_name = None
        self._called_log_level = self._log_level
        self._section_counter += 1
        return self

    def __exit__(self, *args):
        section_name = self._section_name_stack.pop()
        start = self._section_start_stack.pop()
        log_level = self._section_log_level_stack.pop()

        end = timer()
        interval = end - start
        self.profile_list.append((section_name, interval))

        if self._logger is not None:
            self._logger.log(log_level, "%s took %.4f s", section_name, interval)
