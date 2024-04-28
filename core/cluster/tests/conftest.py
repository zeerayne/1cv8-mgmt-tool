import random
import re
from unittest.mock import Mock, PropertyMock

import pytest
from pytest_mock import MockerFixture

from surrogate import surrogate

random.seed(0)


@pytest.fixture()
def mock_infobase_version():
    return f"{random.randint(1,12)}.{random.randint(0,5)}.{random.randint(10,200)}"


@pytest.fixture()
def mock_excluded_infobases(mocker: MockerFixture, infobases):
    excluded_infobases = [infobases[-1]]
    mocker.patch("conf.settings.V8_INFOBASES_EXCLUDE", new_callable=PropertyMock(return_value=excluded_infobases))
    return excluded_infobases


@pytest.fixture()
def mock_only_infobases(mocker: MockerFixture, infobases):
    only_infobases = infobases[:-1]
    mocker.patch("conf.settings.V8_INFOBASES_ONLY", new_callable=PropertyMock(return_value=only_infobases))
    return only_infobases


@surrogate("win32com.client")
@pytest.fixture()
def mock_win32com_client_dispatch(mocker: MockerFixture):
    import win32com.client as win32com_client

    v8COMConnectorMock = mocker.patch.object(win32com_client, "Dispatch", create=True, return_value=Mock())
    type(v8COMConnectorMock.return_value).ConnectWorkingProcess = Mock()
    return v8COMConnectorMock


@pytest.fixture()
def mock_infobases_com_obj(infobases):
    infobases_com_obj = []
    for ib in infobases:
        infobase_com_obj_mock = Mock()
        type(infobase_com_obj_mock).Name = ib
        infobases_com_obj.append(infobase_com_obj_mock)
    return Mock(return_value=infobases_com_obj)


@pytest.fixture()
def mock_connect_agent(mock_win32com_client_dispatch, mock_infobases_com_obj):
    agent_connection_mock = Mock()

    type(agent_connection_mock.return_value).GetInfoBases = mock_infobases_com_obj
    type(agent_connection_mock.return_value).Authenticate = Mock()
    type(agent_connection_mock.return_value).GetClusters = Mock(return_value=["test_cluster01", "test_cluster02"])

    working_process_mock = Mock()
    type(working_process_mock).MainPort = random.randint(1000, 2000)
    type(agent_connection_mock.return_value).GetWorkingProcesses = Mock(return_value=[working_process_mock])

    type(agent_connection_mock.return_value).GetInfoBaseSessions = Mock(
        side_effect=lambda cluster, info_base_short: [f"test_{info_base_short.Name}_session_{i}" for i in range(1, 5)]
    )

    type(mock_win32com_client_dispatch.return_value).ConnectAgent = agent_connection_mock
    return agent_connection_mock


@pytest.fixture()
def mock_connect_working_process(mock_win32com_client_dispatch, mock_infobases_com_obj):
    working_process_connection_mock = Mock()
    type(working_process_connection_mock.return_value).AuthenticateAdmin = Mock()
    type(working_process_connection_mock.return_value).AddAuthentication = Mock()
    type(working_process_connection_mock.return_value).GetInfoBases = mock_infobases_com_obj
    type(working_process_connection_mock.return_value).UpdateInfoBase = Mock()

    type(mock_win32com_client_dispatch.return_value).ConnectWorkingProcess = working_process_connection_mock
    return working_process_connection_mock


@pytest.fixture()
def mock_external_connection(mock_win32com_client_dispatch, mock_infobase_version):
    def external_connection_mock_side_effect(connection_string):
        infobase_name = re.search(r'Ref="(?P<ref>[\w\d\-_]+)"', connection_string).group("ref")
        side_effect_mock = Mock()
        side_effect_mock.Metadata.Version = mock_infobase_version
        side_effect_mock.Metadata.Name = infobase_name
        return side_effect_mock

    external_connection_mock = Mock(side_effect=external_connection_mock_side_effect)
    type(mock_win32com_client_dispatch.return_value).Connect = external_connection_mock
    return external_connection_mock
