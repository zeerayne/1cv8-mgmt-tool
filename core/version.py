import os
from packaging.version import Version
from typing import List


def get_version_from_string(version_str: str) -> Version:
    return Version(version_str)


def find_last_version(versions: List[str]) -> Version:
    pkg_versions = [get_version_from_string(v) for v in versions]
    max_version = max(pkg_versions)
    return max_version


def find_platform_last_version(platform_path: str) -> Version:
    platforms = [name for name in os.listdir(platform_path)
        if (os.path.isdir(os.path.join(platform_path, name)) and name[0].isdigit())
    ]
    last_platform_version = find_last_version(platforms)
    return last_platform_version
