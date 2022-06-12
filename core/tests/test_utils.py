from datetime import datetime

import pytest

from conf import settings
from core.utils import (
    get_platform_full_path, get_formatted_current_datetime, get_formatted_date, 
    get_ib_name_with_separator, get_ib_and_time_string, append_file_extension_to_string
)


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


def test_get_ib_name_with_separator_contains_ib_name(infobase):
    """
    Infobase name exists in `ib_name_with_separator` string
    """
    result = get_ib_name_with_separator(infobase)
    assert f'{infobase}' in result


def test_get_ib_name_with_separator_containt_separator(infobase):
    """
    `settings.FILE_SEPARATOR` exists at the end of `ib_name_with_separator` string
    """
    result = get_ib_name_with_separator(infobase)
    assert result.endswith(settings.FILENAME_SEPARATOR)


def test_get_ib_and_time_string_has_infobase_name_in_result_string(infobase):
    """
    Infobase name exists in `ib_and_time` string
    """
    result = get_ib_and_time_string(infobase)
    assert f'{infobase}' in result


@pytest.mark.freeze_time('2022-01-01 12:01:01')
def test_get_ib_and_time_string_has_properly_formatted_datetime_in_result_string(infobase):
    """
    Datetime is properly formatted in `ib_and_time` string
    """
    result = get_ib_and_time_string(infobase)
    assert get_formatted_current_datetime() in result


@pytest.mark.freeze_time('2022-01-01 12:01:01')
def test_get_ib_and_time_string_uses_underscore(infobase):
    """
    Between infobase name and datetime `settings.FILENAME_SEPARATOR` is used
    """
    result = get_ib_and_time_string(infobase)
    assert f'{infobase}{settings.FILENAME_SEPARATOR}{get_formatted_current_datetime()}' in result


def test_append_file_extension_to_string_starts_with_filename():
    """
    Filename with extension starts with filename
    """
    filename = 'test_filename'
    result = append_file_extension_to_string(filename, 'testext')
    assert result.startswith(filename)


def test_append_file_extension_to_string_ends_with_filename():
    """
    Filename with extension ends with extension
    """
    extension = 'testext'
    result = append_file_extension_to_string('test_filename', extension)
    assert result.endswith(extension)


def test_append_file_extension_to_string_contains_dot():
    """
    Filename with extension contains dot
    """
    result = append_file_extension_to_string('test_filename', 'testext')
    assert '.' in result
