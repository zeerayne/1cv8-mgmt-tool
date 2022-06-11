from packaging.version import Version

from pytest_mock import MockerFixture

from core.version import get_version_from_string, find_last_version, find_platform_last_version


def test_get_version_from_string_returns_version(mock_platform_version):
    """
    Correct `packaging.version.Version` object is returned
    """
    result = get_version_from_string(mock_platform_version)
    assert isinstance(result, Version)


def test_get_version_from_string_version_matches(mock_platform_version):
    """
    Version matches
    """
    result = get_version_from_string(mock_platform_version)
    assert result == Version(mock_platform_version)


def test_find_last_version_finds_correctly(mock_platform_versions, mock_platform_last_version):
    """
    Last version is found correctly
    """
    result = find_last_version(mock_platform_versions)
    assert result == Version(mock_platform_last_version)


def test_find_platform_last_version_finds_correctly(mocker: MockerFixture, mock_platform_versions, mock_platform_last_version):
    """
    Last platform version is found correctly
    """
    mocker.patch('os.listdir', return_value=mock_platform_versions + ['test_common', 'test_conf', 'test_srvinfo'])
    mocker.patch('os.path.isdir', return_value=True)

    result = find_platform_last_version('')
    assert result == Version(mock_platform_last_version)
