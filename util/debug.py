import os


DEBUG_MONKEY_PATCH = '.debug'


def is_debug():
    return os.path.isfile(DEBUG_MONKEY_PATCH)
