from utils.common import sizeof_fmt


def test_sizeof_fmt_below_radix_value():
    """
    Check if below radix values are formatted correctly
    """
    result = sizeof_fmt(512)
    assert result == '512.0B'


def test_sizeof_fmt_above_radix_value():
    """
    Check if above radix values are formatted correctly
    """
    result = sizeof_fmt(1024)
    assert result == '1.0KiB'


def test_sizeof_fmt_big_value():
    """
    Check if big values (>= radix ** 9) are formatted correctly
    """
    result = sizeof_fmt(1024 ** 9)
    assert result == '1024.0YiB'

def test_sizeof_fmt_custom_radix():
    """
    Check if values with custom radix are formatted correctly
    """
    result = sizeof_fmt(2000, radix = 1000)
    assert result == '2.0KiB'


def test_sizeof_fmt_custom_unit():
    """
    Check if values with custom unit are formatted correctly
    """
    result = sizeof_fmt(1024 * 1.5, suffix = 'Q')
    assert result == '1.5KiQ'


def test_sizeof_fmt_custom_unit():
    """
    Check if values with custom radix suffix are formatted correctly
    """
    result = sizeof_fmt(1024 ** 2 * 4.7, radix_suffix = '')
    assert result == '4.7MB'
