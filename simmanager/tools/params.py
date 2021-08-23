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
