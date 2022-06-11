from datetime import datetime

import pytest

from conf import settings

from core.utils import get_platform_full_path, get_formatted_current_datetime, get_formatted_date, get_ib_and_time_string


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
def test_get_formatted_current_datetime():
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


def test_get_ib_and_time_string_has_infobase_name_in_result_string(infobases):
    """
    Infobase name exists in `ib_and_time` string
    """
    infobase = infobases[0]
    result = get_ib_and_time_string(infobase)
    assert f'{infobase}' in result


@pytest.mark.freeze_time('2022-01-01 12:01:01')
def test_get_ib_and_time_string_has_properly_formatted_datetime_in_result_string(infobases):
    """
    Datetime is properly formatted in `ib_and_time` string
    """
    infobase = infobases[0]
    result = get_ib_and_time_string(infobase)
    assert get_formatted_current_datetime() in result


@pytest.mark.freeze_time('2022-01-01 12:01:01')
def test_get_ib_and_time_string_uses_underscore(infobases):
    """
    Between infobase name and datetime underscore is used
    """
    infobase = infobases[0]
    result = get_ib_and_time_string(infobase)
    assert f'{infobase}_{get_formatted_current_datetime()}' in result
