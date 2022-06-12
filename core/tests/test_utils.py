from datetime import datetime
from unittest.mock import AsyncMock

import pytest

try:
    import pywintypes
except ImportError:
    from surrogate import surrogate
    surrogate('pywintypes').prepare()
    import pywintypes
    pywintypes.com_error = Exception

from conf import settings
from core import types as core_types
from core.exceptions import V8Exception
from core.utils import (
    get_platform_full_path, get_formatted_current_datetime, get_formatted_date, 
    get_ib_name_with_separator, get_ib_and_time_string, append_file_extension_to_string,
    get_ib_and_time_filename, get_info_bases, get_info_base_credentials, path_leaf,
    com_func_wrapper
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


def test_get_ib_and_time_filename_starts_with_ib_name(infobase):
    """
    Infobase filename with time starts with infobase name
    """
    result = get_ib_and_time_filename(infobase, 'testext')
    assert result.startswith(infobase)


@pytest.mark.freeze_time('2022-01-01 12:01:01')
def test_get_ib_and_time_filename_contains_formatted_datetime(infobase):
    """
    Infobase filename with time contains properly formatted datetime
    """
    result = get_ib_and_time_filename(infobase, 'testext')
    assert get_formatted_current_datetime() in result


def test_get_ib_and_time_filename_contains_filename_separator(infobase):
    """
    Infobase filename with time contains filename separator
    """
    result = get_ib_and_time_filename(infobase, 'testext')
    assert settings.FILENAME_SEPARATOR in result


def test_get_ib_and_time_filename_contains_dot(infobase):
    """
    Infobase filename with time contains dot
    """
    result = get_ib_and_time_filename(infobase, 'testext')
    assert '.' in result


def test_get_ib_and_time_filename_ends_with_file_extension(infobase):
    """
    Infobase filename with time ends with extension
    """
    extension = 'testext'
    result = append_file_extension_to_string(infobase, extension)
    assert result.endswith(extension)


def test_get_info_bases_not_returns_excluded_infobases(
    infobases,
    mock_excluded_infobases,
    mock_connect_agent,
    mock_connect_working_process
):
    """
    `get_info_bases` not returns excluded infobases
    """
    result = get_info_bases()
    assert all(excluded_infobase not in result for excluded_infobase in mock_excluded_infobases)


def test_get_info_bases_returns_all_but_excluded_infobases(
    infobases,
    mock_excluded_infobases,
    mock_connect_agent,
    mock_connect_working_process
):
    """
    `get_info_bases` returns all but excluded infobases
    """
    result = get_info_bases()
    assert all(infobase in result for infobase in set(infobases) - set(mock_excluded_infobases))


def test_get_info_base_credentials_for_infobase(infobase, mock_infobases_credentials):
    """
    Infobase credentials are gained for proper infobase
    """
    result = get_info_base_credentials(infobase)
    assert result == mock_infobases_credentials[infobase]


def test_get_info_base_credentials_fallback_to_default(infobase):
    """
    Infobase credentials falls back yo default if no explicit record for infobase
    """
    result = get_info_base_credentials(infobase)
    assert result == settings.V8_INFO_BASES_CREDENTIALS['default']


def test_path_leaf_on_full_path():
    """
    Filename extracted correctly from full path
    """
    filename = 'test.exe'
    path = rf'C:\Test Folder\{filename}'
    result = path_leaf(path)
    assert result == filename


def test_path_leaf_on_relative_path():
    """
    Filename extracted correctly from relative path
    """
    filename = 'test.exe'
    path = rf'Test Folder\{filename}'
    result = path_leaf(path)
    assert result == filename


def test_path_leaf_on_filename():
    """
    Filename extracted correctly if only filename passed
    """
    filename = 'test.exe'
    result = path_leaf(filename)
    assert result == filename


@pytest.mark.asyncio
async def test_com_func_wrapper_awaits_inner_func(infobase):
    """
    `com_func_wrapper` awaits inner coroutine
    """
    coroutine_mock = AsyncMock(side_effect=lambda ib_name: core_types.InfoBaseTaskResultBase(ib_name, True))
    await com_func_wrapper(coroutine_mock, infobase)
    coroutine_mock.assert_awaited()


@pytest.mark.asyncio
async def test_com_func_wrapper_returns_value_of_inner_func(infobase):
    """
    `com_func_wrapper` returns value from inner coroutine
    """
    coroutine_mock = AsyncMock(side_effect=lambda ib_name: core_types.InfoBaseTaskResultBase(ib_name, True))
    result = await com_func_wrapper(coroutine_mock, infobase)
    assert result.infobase_name == infobase and result.succeeded == True


@pytest.mark.asyncio
async def test_com_func_wrapper_handle_com_error(infobase, mock_connect_agent, mock_connect_working_process):
    """
    `com_func_wrapper` returns value when com error raised
    """
    def raise_com_error(*args):
        raise pywintypes.com_error

    coroutine_mock = AsyncMock(side_effect=raise_com_error)
    result = await com_func_wrapper(coroutine_mock, infobase)
    assert result.infobase_name == infobase and result.succeeded == False


@pytest.mark.asyncio
async def test_com_func_wrapper_handle_v8_exception(infobase, mock_connect_agent, mock_connect_working_process):
    """
    `com_func_wrapper` returns value when V8Exception raised
    """
    def raise_v8_exception(*args):
        raise V8Exception

    coroutine_mock = AsyncMock(side_effect=raise_v8_exception)
    result = await com_func_wrapper(coroutine_mock, infobase)
    assert result.infobase_name == infobase and result.succeeded == False
