from datetime import datetime, timedelta
from unittest.mock import AsyncMock, mock_open

import pytest
from pytest_mock import MockerFixture

try:
    import pywintypes
except ImportError:
    from surrogate import surrogate

    surrogate("pywintypes").prepare()
    import pywintypes

    pywintypes.com_error = Exception

from conf import settings
from core.utils import (
    append_file_extension_to_string,
    get_formatted_current_datetime,
    get_formatted_date_for_1cv8,
    get_ib_and_time_filename,
    get_ib_and_time_string,
    get_ib_name_with_separator,
    get_info_base_credentials,
    get_info_bases,
    get_infobase_glob_pattern,
    get_1cv8_service_full_path,
    path_leaf,
    read_file_content,
    remove_old_files_by_pattern,
)


def test_get_1cv8_service_full_path_contains_platform_version(mock_os_platform_path, mock_platform_last_version):
    """
    Full path to platform binary contains last platform version directory
    """
    result = get_1cv8_service_full_path()
    assert mock_platform_last_version in result


def test_get_1cv8_service_full_path_contains_executable(mock_os_platform_path):
    """
    Full path to platform binary contains executable file
    """
    result = get_1cv8_service_full_path()
    assert "1cv8" in result


@pytest.mark.freeze_time("2022-01-01 12:01:01")
def test_get_formatted_current_datetime():
    """
    Datetime is formatted according to settings defined format
    """
    result = get_formatted_current_datetime()
    assert result == datetime.now().strftime(settings.DATETIME_FORMAT)


def test_get_formatted_date_for_1cv8(mock_datetime):
    """
    Date for 1CV8 is formatted according to settings defined format
    """
    result = get_formatted_date_for_1cv8(mock_datetime)
    assert result == mock_datetime.strftime(settings.DATE_FORMAT_1CV8)


def test_get_ib_name_with_separator_contains_ib_name(infobase):
    """
    Infobase name exists in `ib_name_with_separator` string
    """
    result = get_ib_name_with_separator(infobase)
    assert f"{infobase}" in result


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
    assert f"{infobase}" in result


@pytest.mark.freeze_time("2022-01-01 12:01:01")
def test_get_ib_and_time_string_has_properly_formatted_datetime_in_result_string(
    infobase,
):
    """
    Datetime is properly formatted in `ib_and_time` string
    """
    result = get_ib_and_time_string(infobase)
    assert get_formatted_current_datetime() in result


@pytest.mark.freeze_time("2022-01-01 12:01:01")
def test_get_ib_and_time_string_uses_underscore(infobase):
    """
    Between infobase name and datetime `settings.FILENAME_SEPARATOR` is used
    """
    result = get_ib_and_time_string(infobase)
    assert f"{infobase}{settings.FILENAME_SEPARATOR}{get_formatted_current_datetime()}" in result


def test_append_file_extension_to_string_starts_with_filename():
    """
    Filename with extension starts with filename
    """
    filename = "test_filename"
    result = append_file_extension_to_string(filename, "testext")
    assert result.startswith(filename)


def test_append_file_extension_to_string_ends_with_filename():
    """
    Filename with extension ends with extension
    """
    extension = "testext"
    result = append_file_extension_to_string("test_filename", extension)
    assert result.endswith(extension)


def test_append_file_extension_to_string_contains_dot():
    """
    Filename with extension contains dot
    """
    result = append_file_extension_to_string("test_filename", "testext")
    assert "." in result


def test_get_ib_and_time_filename_starts_with_ib_name(infobase):
    """
    Infobase filename with time starts with infobase name
    """
    result = get_ib_and_time_filename(infobase, "testext")
    assert result.startswith(infobase)


@pytest.mark.freeze_time("2022-01-01 12:01:01")
def test_get_ib_and_time_filename_contains_formatted_datetime(infobase):
    """
    Infobase filename with time contains properly formatted datetime
    """
    result = get_ib_and_time_filename(infobase, "testext")
    assert get_formatted_current_datetime() in result


def test_get_ib_and_time_filename_contains_filename_separator(infobase):
    """
    Infobase filename with time contains filename separator
    """
    result = get_ib_and_time_filename(infobase, "testext")
    assert settings.FILENAME_SEPARATOR in result


def test_get_ib_and_time_filename_contains_dot(infobase):
    """
    Infobase filename with time contains dot
    """
    result = get_ib_and_time_filename(infobase, "testext")
    assert "." in result


def test_get_ib_and_time_filename_ends_with_file_extension(infobase):
    """
    Infobase filename with time ends with extension
    """
    extension = "testext"
    result = append_file_extension_to_string(infobase, extension)
    assert result.endswith(extension)


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
    assert result == settings.V8_INFOBASES_CREDENTIALS["default"]


def test_path_leaf_on_full_path():
    """
    Filename extracted correctly from full path
    """
    filename = "test.exe"
    path = rf"C:\Test Folder\{filename}"
    result = path_leaf(path)
    assert result == filename


def test_path_leaf_on_relative_path():
    """
    Filename extracted correctly from relative path
    """
    filename = "test.exe"
    path = rf"Test Folder\{filename}"
    result = path_leaf(path)
    assert result == filename


def test_path_leaf_on_filename():
    """
    Filename extracted correctly if only filename passed
    """
    filename = "test.exe"
    result = path_leaf(filename)
    assert result == filename


def test_read_file_content_returns_content(mocker: MockerFixture):
    """
    Content is returned from readed file
    """
    content = "test_file_content"
    mocker.patch("builtins.open", mock_open(read_data=content))
    result = read_file_content("")
    assert result == content


def test_read_file_content_rstrips_content(mocker: MockerFixture):
    """
    Content readed from file is rstripped
    """
    content = "test_file_content\n"
    mocker.patch("builtins.open", mock_open(read_data=content))
    result = read_file_content("")
    assert result == content.rstrip()


def test_read_file_gets_correct_encoding(mocker: MockerFixture):
    """
    File encoding is passed to `open`
    """
    content = "test_file_content"
    encoding = "test_encoding"
    builtin_open_mock = mocker.patch("builtins.open", mock_open(read_data=content))
    read_file_content("", encoding)
    builtin_open_mock.assert_called_with("", "r", encoding=encoding)


@pytest.mark.asyncio
async def test_remove_old_files_by_pattern_removes_old_files(mocker: MockerFixture):
    """
    Old files are removed according to retention policy
    """
    retention_days = 1
    files = ["test_file1", "test_file2"]
    mocker.patch("glob.glob", return_value=files)
    mocker.patch(
        "os.path.getmtime",
        return_value=(datetime.now() - timedelta(days=retention_days + 1)).timestamp(),
    )
    aioremove_mock = mocker.patch("aiofiles.os.remove", return_value=AsyncMock())
    await remove_old_files_by_pattern("", retention_days)
    assert aioremove_mock.await_count == len(files)


@pytest.mark.asyncio
async def test_remove_old_files_by_pattern_not_removes_new_files(mocker: MockerFixture):
    """
    New files are not removed according to retention policy
    """
    retention_days = 1
    files = ["test_file1", "test_file2"]
    mocker.patch("glob.glob", return_value=files)
    mocker.patch("os.path.getmtime", return_value=datetime.now().timestamp())
    aioremove_mock = mocker.patch("aiofiles.os.remove", return_value=AsyncMock())
    await remove_old_files_by_pattern("", retention_days)
    aioremove_mock.assert_not_awaited()


def test_get_infobase_glob_pattern_contains_infobase_name(infobase):
    """
    `get_infobase_glob_pattern` result contains infobase name
    """
    result = get_infobase_glob_pattern(infobase)
    assert infobase in result


def test_get_infobase_glob_pattern_contains_file_extension(infobase):
    """
    `get_infobase_glob_pattern` result contains file extension, if provided
    """
    file_extension = "test_extension"
    result = get_infobase_glob_pattern(infobase, file_extension)
    assert file_extension in result


def test_get_infobase_glob_pattern_uses_infobase_filename_separator(infobase):
    """
    `get_infobase_glob_pattern` result contains infobase filename separator
    """
    result = get_infobase_glob_pattern(infobase)
    assert get_ib_name_with_separator(infobase) in result


def test_get_info_bases_returns_infobases_from_cluster(mock_cluster_com_infobases, infobases):
    """
    `get_info_bases` returns infobases list from cluster
    """
    result = get_info_bases()
    assert result == infobases
