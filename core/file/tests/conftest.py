from unittest.mock import Mock

import pytest
from pytest_mock import MockerFixture

from surrogate import surrogate


@surrogate("win32com.client")
@pytest.fixture()
def mock_win32com_client_dispatch(mocker: MockerFixture):
    import win32com.client as win32com_client

    return mocker.patch.object(win32com_client, "Dispatch", create=True, return_value=Mock())


@pytest.fixture()
def mock_external_connection(mock_win32com_client_dispatch, mock_configuration_metadata):
    def external_connection_mock_side_effect(connection_string):
        side_effect_mock = Mock()
        side_effect_mock.Metadata.Name = mock_configuration_metadata[0]
        side_effect_mock.Metadata.Version = mock_configuration_metadata[1]
        return side_effect_mock

    external_connection_mock = Mock(side_effect=external_connection_mock_side_effect)
    type(mock_win32com_client_dispatch.return_value).Connect = external_connection_mock
    return external_connection_mock
