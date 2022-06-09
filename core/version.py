import os
from distutils.version import LooseVersion


def get_version_from_string(version_str):
    return LooseVersion(version_str)


def find_last_version(versions):
    loose_versions = [get_version_from_string(v) for v in versions]
    max_version = max(loose_versions)
    return str(max_version)


def find_platform_last_version(platform_path):
    platforms = [name for name in os.listdir(platform_path)
                 if (os.path.isdir(os.path.join(platform_path, name)) and name[0].isdigit())
                 ]
    last_platform_version = find_last_version(platforms)
    return last_platform_version
