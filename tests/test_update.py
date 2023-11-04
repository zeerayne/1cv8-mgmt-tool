from pytest_mock import MockerFixture

from update import (
    _find_suitable_manifests,
    _get_suitable_manifest,
    get_name_and_version_from_manifest,
    get_updatable_versions,
)


def test_get_name_and_version_from_manifest_returns_name_from_manifest(mock_configuration_manifest):
    """
    Configuration name is extracted from manifest
    """
    result = get_name_and_version_from_manifest("")
    assert result[0] == mock_configuration_manifest[0]


def test_get_name_and_version_from_manifest_returns_version_from_manifest(mock_configuration_manifest):
    """
    Configuration version is extracted from manifest
    """
    result = get_name_and_version_from_manifest("")
    assert result[1] == mock_configuration_manifest[1]


def test_get_updatable_versions_returns_versions_from_updinfo(mock_configuration_manifest_updinfo):
    """
    Updatable versions are extracted from updinfo
    """
    result = get_updatable_versions("")
    assert result == mock_configuration_manifest_updinfo


def test_find_suitable_manifests_returns_updated_when_exists(
    mocker: MockerFixture, mock_configuration_metadata, mock_configuration_manifest, mock_configuration_manifest_updinfo
):
    """
    Applicable update manifest is found
    """
    mocker.patch("update.get_name_and_version_from_manifest", return_value=mock_configuration_manifest)
    mocker.patch("update.get_updatable_versions", return_value=mock_configuration_manifest_updinfo)
    result = _find_suitable_manifests(
        ["manifest_test_path/1/1cv8.mft"], mock_configuration_metadata[0], mock_configuration_metadata[1]
    )
    assert len(result) == 1


def test_find_suitable_manifests_returns_correct_manifest_filename(
    mocker: MockerFixture, mock_configuration_metadata, mock_configuration_manifest, mock_configuration_manifest_updinfo
):
    """
    Applicable update manifest filename is correct
    """
    manifest_filename = "manifest_test_path/1/1cv8.mft"
    mocker.patch("update.get_name_and_version_from_manifest", return_value=mock_configuration_manifest)
    mocker.patch("update.get_updatable_versions", return_value=mock_configuration_manifest_updinfo)
    result = _find_suitable_manifests(
        [manifest_filename], mock_configuration_metadata[0], mock_configuration_metadata[1]
    )
    assert result[0][0] == manifest_filename


def test_find_suitable_manifests_returns_correct_manifest_version(
    mocker: MockerFixture, mock_configuration_metadata, mock_configuration_manifest, mock_configuration_manifest_updinfo
):
    """
    Applicable update manifest version is correct
    """
    manifest_filename = "manifest_test_path/1/1cv8.mft"
    mocker.patch("update.get_name_and_version_from_manifest", return_value=mock_configuration_manifest)
    mocker.patch("update.get_updatable_versions", return_value=mock_configuration_manifest_updinfo)
    result = _find_suitable_manifests(
        [manifest_filename], mock_configuration_metadata[0], mock_configuration_metadata[1]
    )
    assert result[0][1] == mock_configuration_manifest[1]


def test_find_suitable_manifests_returns_empty_list_when_no_manifests_are_applicable(
    mocker: MockerFixture,
    mock_configuration_metadata,
    mock_configuration_manifest_new,
    mock_configuration_manifest_updinfo_new,
):
    """
    `_find_suitable_manifests` returns empty list when no manifests are applicable
    """
    manifest_filename = "manifest_test_path/1/1cv8.mft"
    mocker.patch("update.get_name_and_version_from_manifest", return_value=mock_configuration_manifest_new)
    mocker.patch("update.get_updatable_versions", return_value=mock_configuration_manifest_updinfo_new)
    result = _find_suitable_manifests(
        [manifest_filename], mock_configuration_metadata[0], mock_configuration_metadata[1]
    )
    assert len(result) == 0


def test_get_suitable_manifest_returns_applicable_manifest(
    mocker: MockerFixture, mock_configuration_manifest, mock_configuration_manifest_new
):
    """
    `_get_suitable_manifest` picks most recent update manifest
    """
    manifest1 = ("manifest_test_path/1/1cv8.mft", mock_configuration_manifest[1])
    manifest2 = ("manifest_test_path/2/1cv8.mft", mock_configuration_manifest_new[1])
    mocker.patch("update._find_suitable_manifests", return_value=[manifest1, manifest2])
    result = _get_suitable_manifest(None, None, None)
    assert result == manifest2
