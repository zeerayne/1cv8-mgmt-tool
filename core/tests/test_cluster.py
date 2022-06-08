from core.cluster import ClusterControlInterface


def test_cluster_control_interface_initialization(mock_win32com_client_dispatch):
    """
    ClusterControlInterface instance is initialized sucessfully 
    """
    ClusterControlInterface()
    assert mock_win32com_client_dispatch.called_once()


def test_cluster_control_interface_connect_agent(mock_connect_agent):
    """
    `get_agent_connection` makes COM-object call
    """
    ClusterControlInterface().get_agent_connection()
    assert mock_connect_agent.called_once()


def test_cluster_control_interface_get_cluster(mock_get_clusters):
    """
    `get_cluster` makes COM-object call
    """
    cci = ClusterControlInterface()
    agent_connection = cci.get_agent_connection()
    cci.get_cluster(agent_connection)
    assert mock_get_clusters.called_once()


def test_cluster_control_interface_cluster_auth(mock_get_clusters, mock_cluster_auth):
    """
    `cluster_auth` makes COM-object call
    """
    cci = ClusterControlInterface()
    agent_connection = cci.get_agent_connection()
    cluster = cci.get_cluster(agent_connection)
    cci.cluster_auth(agent_connection, cluster)
    assert mock_cluster_auth.called_once()
