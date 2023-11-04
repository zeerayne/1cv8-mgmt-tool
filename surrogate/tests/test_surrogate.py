import unittest

import pytest

from surrogate import surrogate


def imports():
    import my
    import my.module
    import my.module.one
    import my.module.two
    from my import module
    from my.module import one, two

    return True


class TestSurrogateModuleStubs(unittest.TestCase):
    def test_without_surrogating(self):
        with pytest.raises(ImportError):
            imports()

    def test_surrogating(self):
        @surrogate("my")
        @surrogate("my.module.one")
        @surrogate("my.module.two")
        def stubbed():
            imports()

        try:
            stubbed()
        except Exception as e:
            raise Exception(f"Modules are not stubbed correctly: {e}")

    def test_context_manager(self):
        with surrogate("my"), surrogate("my.module.one"), surrogate("my.module.two"):
            imports()
