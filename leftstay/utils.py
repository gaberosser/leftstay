from itertools import islice
import os


def chunk(it, size):
    it = iter(it)
    return iter(lambda: tuple(islice(it, size)), ())

