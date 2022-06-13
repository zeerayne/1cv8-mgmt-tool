from utils.postgres import POSTGRES_DEFAULT_PORT, get_postgres_host_and_port


def test_get_postgres_host_and_port_extract_host_with_port():
    """
    Postgres host is extracted correctly from string with port
    """
    host = '192.168.1.100'
    port = '5555'
    result = get_postgres_host_and_port(f'{host}:{port}')
    assert result[0] == host


def test_get_postgres_host_and_port_extract_host_without_port():
    """
    Postgres host is extracted correctly from string without port
    """
    host = '192.168.1.100'
    result = get_postgres_host_and_port(f'{host}')
    assert result[0] == host


def test_get_postgres_host_and_port_extract_port_with_port():
    """
    Postgres port is extracted correctly from string with port
    """
    host = '192.168.1.100'
    port = '5555'
    result = get_postgres_host_and_port(f'{host}:{port}')
    assert result[1] == port


def test_get_postgres_host_and_port_extract_port_without_port():
    """
    Postgres port is extracted correctly from string without port
    """
    host = '192.168.1.100'
    result = get_postgres_host_and_port(f'{host}')
    assert result[1] == POSTGRES_DEFAULT_PORT
