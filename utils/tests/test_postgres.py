import pytest

from conf import settings
from utils.postgres import POSTGRES_DEFAULT_PORT, get_postgres_host_and_port, prepare_postgres_connection_vars


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


def test_prepare_postgres_connection_vars_raises_value_error_for_non_postgres_dbms():
    """
    `prepare_postgres_connection_vars` raises ValueError if dbms is not postgres
    """
    with pytest.raises(ValueError):
        prepare_postgres_connection_vars('localhost', 'MSSQL', 'template1', 'postgres')


def test_prepare_postgres_connection_vars_raises_key_error_if_no_credentials_found():
    """
    `prepare_postgres_connection_vars` raises KeyError if credentials for user@host not found
    """
    with pytest.raises(KeyError):
        prepare_postgres_connection_vars('remotehost', 'postgresql', 'template1', 'postgres')


def test_prepare_postgres_connection_vars_returns_exactly_5_elements():
    """
    `prepare_postgres_connection_vars` returns db_host, db_port, db_name, db_user, db_pwd
    """
    result = prepare_postgres_connection_vars('localhost', 'postgresql', 'template1', 'postgres')
    assert len(result) == 5


def test_prepare_postgres_connection_vars_returns_correct_host():
    """
    `prepare_postgres_connection_vars` returns correct `db_host` value
    """
    host = 'localhost'
    result = prepare_postgres_connection_vars(host, 'postgresql', 'template1', 'postgres')
    assert result[0] == host


def test_prepare_postgres_connection_vars_returns_correct_port():
    """
    `prepare_postgres_connection_vars` returns correct `db_port` value
    """
    result = prepare_postgres_connection_vars('localhost', 'postgresql', 'template1', 'postgres')
    assert result[1] == POSTGRES_DEFAULT_PORT


def test_prepare_postgres_connection_vars_returns_correct_db_name():
    """
    `prepare_postgres_connection_vars` returns correct `db_name` value
    """
    db_name = 'template1'
    result = prepare_postgres_connection_vars('localhost', 'postgresql', db_name, 'postgres')
    assert result[2] == db_name


def test_prepare_postgres_connection_vars_returns_correct_db_user():
    """
    `prepare_postgres_connection_vars` returns correct `db_user` value
    """
    db_user = 'postgres'
    result = prepare_postgres_connection_vars('localhost', 'postgresql', 'template1', db_user)
    assert result[3] == db_user


def test_prepare_postgres_connection_vars_returns_correct_db_password():
    """
    `prepare_postgres_connection_vars` returns correct `db_pwd` value
    """
    host = 'localhost'
    db_user = 'postgres'
    result = prepare_postgres_connection_vars(host, 'postgresql', 'template1', db_user)
    assert result[4] == settings.PG_CREDENTIALS[f'{db_user}@{host}']
