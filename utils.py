def get_nested_dict(d: dict, key: str, msg='', sep='.'):
    """Safely gets a key from a nest dictionary.

       This function looks for a segmented key in a nested dictionary. If it
       does not find a key along the sement, it will return msg, which defaults
    to ''. This function will not normally throw an exception.

       It takes an optional parameter as the segment marker. By default it is
       set to '.'.
    """
    if d is None or key is None:
        return msg

    try:

        curr_d = d
        for seg in key.split(sep):
            curr_d = curr_d[seg]

    except KeyError:
        return msg

    return curr_d


def list_to_csv(l: list, fn=None):
    if fn is not None:
        with open(fn, 'w') as f:
            for row in l:
                f.write(','.join(map(str, row)))
                f.write('\n')
    else:
        for row in l:
            print(','.join(map(str, row)))
