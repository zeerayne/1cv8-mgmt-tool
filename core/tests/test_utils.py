from datetime import datetime

import pytest

from conf import settings

from core.utils import get_platform_full_path, get_formatted_current_datetime, get_formatted_date


def test_get_platform_full_path_contains_platform_version(mock_os_platform_path, mock_platform_last_version):
    """
    Full path to platform binary contains last platform version directory
    """
    result = get_platform_full_path()
    assert mock_platform_last_version in result


def test_get_platform_full_path_contains_executable(mock_os_platform_path):
    """
    Full path to platform binary contains executable file
    """
    result = get_platform_full_path()
    assert '1cv8.exe' in result


@pytest.mark.freeze_time('2022-01-01 12:01:01')
def test_get_formatted_current_datetime(freezer):
    """
    Datetime is formatted according to settings defined format
    """
    result = get_formatted_current_datetime()
    assert result == datetime.now().strftime(settings.DATETIME_FORMAT)


def test_get_formatted_date(mock_datetime):
    """
    Datetime is formatted according to settings defined format
    """
    result = get_formatted_date(mock_datetime)
    assert result == mock_datetime.strftime(settings.DATE_FORMAT)
