from itertools import islice
import os


def chunk(it, size):
    it = iter(it)
    return iter(lambda: tuple(islice(it, size)), ())


def dict_equality(x0, x1, keys=None, return_diff=False):
    """
    Compare the two supplied dictionaries for equality based on the list of keys.
    If no keys supplied, use the intersection
    """
    if keys is None:
        keys = set(x0.keys()).intersection(x1.keys())
    if return_diff:
        diff = {}
        for k in keys:
            if x0[k] != x1[k]:
                diff[k] = (x0[k], x1[k])
        return not bool(len(diff)), diff
    else:
        return all([x0[k] == x1[k] for k in keys])

