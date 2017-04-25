from itertools import islice


def chunk(it, size):
    it = iter(it)
    return iter(lambda: tuple(islice(it, size)), ())


class Singleton(type):
    """
    Declare a singleton class by setting `__metaclass__ = Singleton`
    The effect is that `__call__` is called during instantiation, before `__init__`.
    If an instance already exists, we return that, so only one instance ever exists.
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        # this gets called
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
