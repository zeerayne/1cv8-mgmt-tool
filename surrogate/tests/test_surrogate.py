import unittest

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

    def test_surrogating(self):
        @surrogate('my')
        @surrogate('my.module.one')
        @surrogate('my.module.two')
        def stubbed():
            imports()

        try:
            stubbed()
        except Exception as e:
            raise Exception(f'Modules are not stubbed correctly: {e}')

        with self.assertRaises(ImportError) as e:
            imports()

    def test_context_manager(self):
        with surrogate('my'):
            with surrogate('my.module.one'):
                with surrogate('my.module.two'):
                    imports()
