from unittest.mock import Mock
from pytest_mock import MockerFixture
from core.cluster import ClusterControlInterface


def test_cluster_control_interface_initialization(mock_win32com_client_dispatch):
    """
    ClusterControlInterface instance is initialized sucessfully 
    """
    ClusterControlInterface()
    assert mock_win32com_client_dispatch.called_once()


def test_cluster_control_interface_connect_agent(mock_connect_agent):
    """
    `get_agent_connection` makes `COMConnector.ConnectAgent` call
    """
    ClusterControlInterface().get_agent_connection()
    assert mock_connect_agent.called_once()


def test_cluster_control_interface_get_cluster(mock_connect_agent):
    """
    `get_cluster` makes `IServerAgentConnection.GetClusters` call
    """
    cci = ClusterControlInterface()
    agent_connection = cci.get_agent_connection()
    cci.get_cluster(agent_connection)
    assert mock_connect_agent.return_value.GetClusters.called_once()


def test_cluster_control_interface_cluster_auth(mock_connect_agent):
    """
    `cluster_auth` makes `IClusterInfo.Authenticate` call
    """
    cci = ClusterControlInterface()
    agent_connection = cci.get_agent_connection()
    cluster = cci.get_cluster(agent_connection)
    cci.cluster_auth(agent_connection, cluster)
    assert mock_connect_agent.return_value.Authenticate.called_once()


def test_cluster_control_interface_get_working_process_connection(mock_connect_agent, mock_connect_working_process):
    """
    `get_working_process_connection` makes `COMConnector.ConnectWorkingProcess` call to connect to working process
    """
    cci = ClusterControlInterface()
    cci.get_working_process_connection()
    assert mock_connect_working_process.ConnectWorkingProcess.called_once()


def test_cluster_control_interface_get_working_process_connection_admin_auth(
    mock_connect_agent, 
    mock_connect_working_process
):
    """
    `get_working_process_connection` makes `IWorkingProcessConnection.AuthenticateAdmin` call to authenticate as cluster admin
    """
    cci = ClusterControlInterface()
    cci.get_working_process_connection()
    assert mock_connect_working_process.AuthenticateAdmin.called_once()


def test_cluster_control_interface_get_working_process_connection_info_base_auth(
    mocker: MockerFixture, 
    mock_connect_agent, 
    mock_connect_working_process
):
    """
    `get_working_process_connection_with_info_base_auth` makes `IWorkingProcessConnection.AddAuthentication` 
    call for every infobase credentials
    """
    infobases_credentials = {
        'test_infobase01': ('test_user01', 'test_password01'),
        'test_infobase02': ('test_user02', 'test_password02'),
    }

    setting_mock = mocker.patch('conf.settings.V8_INFO_BASES_CREDENTIALS', return_value=infobases_credentials)
    setting_mock.values = Mock(return_value=infobases_credentials.values())
    cci = ClusterControlInterface()
    cci.get_working_process_connection_with_info_base_auth()
    assert mock_connect_working_process.return_value.AddAuthentication.call_count == len(infobases_credentials)


def test_cluster_control_interface_get_info_bases(mock_connect_agent, mock_connect_working_process):
    """
    `get_info_bases` calls `IWorkingProcessConnection.GetInfoBases`
    """
    cci = ClusterControlInterface()
    working_process_connection = cci.get_working_process_connection()
    cci.get_info_bases(working_process_connection)
    mock_connect_working_process.return_value.GetInfoBases.assert_called()


def test_cluster_control_interface_get_info_base(infobases, mock_connect_agent, mock_connect_working_process):
    """
    `get_info_base` finds exact infobase in list
    """
    infobase_name = infobases[0]
    cci = ClusterControlInterface()
    working_process_connection = cci.get_working_process_connection()
    infobase_com_obj = cci.get_info_base(working_process_connection, infobase_name)
    assert infobase_com_obj.Name == infobase_name


def test_cluster_control_interface_get_info_bases_short(mock_connect_agent):
    """
    `get_info_bases_short` calls `IServerAgentConnection.GetInfoBases`
    """
    cci = ClusterControlInterface()
    agent_connection = cci.get_agent_connection()
    cluster = cci.get_cluster(agent_connection)
    cci.get_info_bases_short(agent_connection, cluster)
    mock_connect_agent.return_value.GetInfoBases.assert_called()


def test_cluster_control_interface_get_info_base_short(infobases, mock_connect_agent):
    """
    `get_info_base_short` finds exact infobase in list
    """
    infobase_name = infobases[0]
    cci = ClusterControlInterface()
    agent_connection = cci.get_agent_connection()
    cluster = cci.get_cluster(agent_connection)
    infobase_com_obj = cci.get_info_base_short(agent_connection, cluster, infobase_name)
    assert infobase_com_obj.Name == infobase_name


def test_cluster_control_interface_get_info_base_metadata(infobases, mock_external_connection):
    """
    `get_info_base_metadata` calls `COMConnector.Connect`
    """
    infobase_name = infobases[0]
    cci = ClusterControlInterface()
    cci.get_info_base_metadata(infobase_name, '', '')
    mock_external_connection.assert_called()


def test_cluster_control_interface_get_info_base_metadata_connects_to_correct_infobase(infobases, mock_external_connection):
    """
    `get_info_base_metadata` connects to correct infobase
    """
    infobase_name = infobases[0]
    cci = ClusterControlInterface()
    metadata = cci.get_info_base_metadata(infobase_name, '', '')
    assert metadata[0] == infobase_name
