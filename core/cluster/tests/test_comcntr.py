from unittest.mock import PropertyMock

from pytest_mock import MockerFixture

from conf import settings
from core.cluster.comcntr import ClusterCOMControler
from core.cluster.utils import get_server_agent_address, get_server_agent_port


def test_get_server_agent_address_returns_exact_address_from_settings():
    """
    Server address is exact same as is settings
    """
    result = get_server_agent_address()
    assert result == settings.V8_SERVER_AGENT["address"]


def test_get_server_agent_port_returns_exact_port_from_settings():
    """
    Server port is exact same as is settings
    """
    result = get_server_agent_port()
    assert result == settings.V8_SERVER_AGENT["port"]


def test_get_server_agent_port_is_str():
    """
    Server port is string type
    """
    result = get_server_agent_port()
    assert type(result) is str


def test_cluster_control_interface_initialization(mock_win32com_client_dispatch):
    """
    ClusterCOMControler instance is initialized sucessfully
    """
    ClusterCOMControler()
    mock_win32com_client_dispatch.assert_called_once()


def test_cluster_control_interface_connect_agent(mock_connect_agent):
    """
    `get_agent_connection` makes `COMConnector.ConnectAgent` call
    """
    ClusterCOMControler().get_agent_connection()
    mock_connect_agent.assert_called_once()


def test_cluster_control_interface_get_cluster(mock_connect_agent):
    """
    `get_cluster` makes `IServerAgentConnection.GetClusters` call
    """
    cci = ClusterCOMControler()
    cci.get_cluster()
    mock_connect_agent.return_value.GetClusters.assert_called_once()


def test_cluster_control_interface_cluster_auth(mock_connect_agent):
    """
    `cluster_auth` makes `IClusterInfo.Authenticate` call
    """
    cci = ClusterCOMControler()
    cci.cluster_auth()
    mock_connect_agent.return_value.Authenticate.assert_called_once()


def test_cluster_control_interface_get_working_process_connection(
    mock_win32com_client_dispatch, mock_connect_agent, mock_connect_working_process
):
    """
    `get_working_process_connection` makes `COMConnector.ConnectWorkingProcess` call to connect to working process
    """
    cci = ClusterCOMControler()
    cci.get_working_process_connection()
    mock_win32com_client_dispatch.return_value.ConnectWorkingProcess.assert_called_once()


def test_cluster_control_interface_get_working_process_connection_admin_auth(
    mock_connect_agent, mock_connect_working_process
):
    """
    `get_working_process_connection` makes `IWorkingProcessConnection.AuthenticateAdmin` call
    to authenticate as cluster admin
    """
    cci = ClusterCOMControler()
    cci.get_working_process_connection()
    mock_connect_working_process.return_value.AuthenticateAdmin.assert_called_once()


def test_cluster_control_interface_get_working_process_connection_info_base_auth(
    mocker: MockerFixture, mock_connect_agent, mock_connect_working_process
):
    """
    `get_working_process_connection_with_info_base_auth` makes `IWorkingProcessConnection.AddAuthentication`
    call for every infobase credentials
    """
    infobases_credentials = {
        "test_infobase01": ("test_user01", "test_password01"),
        "test_infobase02": ("test_user02", "test_password02"),
    }
    mocker.patch(
        "conf.settings.V8_INFOBASES_CREDENTIALS",
        new_callable=PropertyMock(return_value=infobases_credentials),
    )
    cci = ClusterCOMControler()
    cci.get_working_process_connection_with_info_base_auth()
    assert mock_connect_working_process.return_value.AddAuthentication.call_count == len(infobases_credentials)


def test_cluster_control_interface_get_cluster_info_bases(mock_connect_agent, mock_connect_working_process):
    """
    `get_cluster_info_bases` calls `IWorkingProcessConnection.GetInfoBases`
    """
    cci = ClusterCOMControler()
    cci.get_cluster_info_bases()
    mock_connect_working_process.return_value.GetInfoBases.assert_called()


def test_cluster_control_interface_get_info_base(infobase, mock_connect_agent, mock_connect_working_process):
    """
    `get_info_base` finds exact infobase in list
    """
    cci = ClusterCOMControler()
    infobase_com_obj = cci.get_info_base(infobase)
    assert infobase_com_obj.Name == infobase


def test_cluster_control_interface_get_cluster_info_bases_short(mock_connect_agent):
    """
    `get_cluster_info_bases_short` calls `IServerAgentConnection.GetInfoBases`
    """
    cci = ClusterCOMControler()
    cluster = cci.get_cluster()
    agent_connection = cci.get_agent_connection()
    cci.get_cluster_info_bases_short(agent_connection, cluster)
    mock_connect_agent.return_value.GetInfoBases.assert_called()


def test_cluster_control_interface_get_info_base_short(infobase, mock_connect_agent):
    """
    `_get_info_base_short` finds exact infobase in list
    """
    cci = ClusterCOMControler()
    cluster = cci.get_cluster()
    agent_connection = cci.get_agent_connection()
    infobase_com_obj = cci._get_info_base_short(agent_connection, cluster, infobase)
    assert infobase_com_obj.Name == infobase


def test_cluster_control_interface_get_info_base_metadata(infobase, mock_external_connection):
    """
    `get_info_base_metadata` calls `COMConnector.Connect`
    """
    cci = ClusterCOMControler()
    cci.get_info_base_metadata(infobase, "", "")
    mock_external_connection.assert_called()


def test_cluster_control_interface_get_info_base_metadata_connects_to_correct_infobase(
    infobase, mock_external_connection
):
    """
    `get_info_base_metadata` connects to correct infobase
    """
    cci = ClusterCOMControler()
    metadata = cci.get_info_base_metadata(infobase, "", "")
    assert metadata[0] == infobase


def test_cluster_control_interface_lock_info_base(infobase, mock_connect_agent, mock_connect_working_process):
    """
    `lock_info_base` calls `IWorkingProcessConnection.UpdateInfoBase`
    """
    cci = ClusterCOMControler()
    infobase_com_obj = cci.lock_info_base(infobase)
    mock_connect_working_process.return_value.UpdateInfoBase.assert_called_with(infobase_com_obj)


def test_cluster_control_interface_lock_info_base_set_sessions_denied(
    infobase, mock_connect_agent, mock_connect_working_process
):
    """
    `lock_info_base` sets `SessionsDenied` param to True
    """
    cci = ClusterCOMControler()
    infobase_com_obj = cci.lock_info_base(infobase)
    assert infobase_com_obj.SessionsDenied is True


def test_cluster_control_interface_lock_info_base_set_scheduled_jobs_denied(
    infobase, mock_connect_agent, mock_connect_working_process
):
    """
    `lock_info_base` sets `ScheduledJobsDenied` param to True
    """
    cci = ClusterCOMControler()
    infobase_com_obj = cci.lock_info_base(infobase)
    assert infobase_com_obj.ScheduledJobsDenied is True


def test_cluster_control_interface_lock_info_base_set_permission_code(
    infobase, mock_connect_agent, mock_connect_working_process
):
    """
    `lock_info_base` sets `PermissionCode` param
    """
    permission_code = "test_permission_code"
    cci = ClusterCOMControler()
    infobase_com_obj = cci.lock_info_base(infobase, permission_code)
    assert infobase_com_obj.PermissionCode == permission_code


def test_cluster_control_interface_lock_info_base_set_denied_message(
    infobase, mock_connect_agent, mock_connect_working_process
):
    """
    `lock_info_base` sets `DeniedMessage` param
    """
    denied_message = "test_denied_message"
    cci = ClusterCOMControler()
    infobase_com_obj = cci.lock_info_base(infobase, message=denied_message)
    assert infobase_com_obj.DeniedMessage == denied_message


def test_cluster_control_interface_unlock_info_base(infobase, mock_connect_agent, mock_connect_working_process):
    """
    `unlock_info_base` calls `IWorkingProcessConnection.UpdateInfoBase`
    """
    cci = ClusterCOMControler()
    infobase_com_obj = cci.unlock_info_base(infobase)
    mock_connect_working_process.return_value.UpdateInfoBase.assert_called_with(infobase_com_obj)


def test_cluster_control_interface_unlock_info_base_set_sessions_denied(
    infobase, mock_connect_agent, mock_connect_working_process
):
    """
    `unlock_info_base` sets `SessionsDenied` param to False
    """
    cci = ClusterCOMControler()
    infobase_com_obj = cci.unlock_info_base(infobase)
    assert infobase_com_obj.SessionsDenied is False


def test_cluster_control_interface_unlock_info_base_set_scheduled_jobs_denied(
    infobase, mock_connect_agent, mock_connect_working_process
):
    """
    `unlock_info_base` sets `ScheduledJobsDenied` param to False
    """
    cci = ClusterCOMControler()
    infobase_com_obj = cci.unlock_info_base(infobase)
    assert infobase_com_obj.ScheduledJobsDenied is False


def test_cluster_control_interface_terminate_info_base_sessions_get_infobase_session(infobase, mock_connect_agent):
    """
    `terminate_info_base_sessions` calls `IServerAgentConnection.GetInfoBaseSessions`
    """
    cci = ClusterCOMControler()
    cci.terminate_info_base_sessions(infobase)
    mock_connect_agent.return_value.GetInfoBaseSessions.assert_called()


def test_cluster_control_interface_terminate_info_base_sessions_terminate_session(infobase, mock_connect_agent):
    """
    `terminate_info_base_sessions` calls `IServerAgentConnection.TerminateSession`
    """
    cci = ClusterCOMControler()
    cci.terminate_info_base_sessions(infobase)
    mock_connect_agent.return_value.TerminateSession.assert_called()


def test_get_info_bases_not_returns_excluded_infobases(
    infobases, mock_excluded_infobases, mock_connect_agent, mock_connect_working_process
):
    """
    `get_info_bases` not returns excluded infobases
    """
    cci = ClusterCOMControler()
    result = cci.get_info_bases()
    assert all(excluded_infobase not in result for excluded_infobase in mock_excluded_infobases)


def test_get_info_bases_returns_all_but_excluded_infobases(
    infobases, mock_excluded_infobases, mock_connect_agent, mock_connect_working_process
):
    """
    `get_info_bases` returns all but excluded infobases
    """
    cci = ClusterCOMControler()
    result = cci.get_info_bases()
    assert all(infobase in result for infobase in set(infobases) - set(mock_excluded_infobases))


def test_get_info_bases_returns_exact_only_infobases(
    infobases, mock_only_infobases, mock_connect_agent, mock_connect_working_process
):
    """
    `get_info_bases` returns exact only infobases
    """
    cci = ClusterCOMControler()
    result = cci.get_info_bases()
    assert all(infobase in mock_only_infobases for infobase in result)
