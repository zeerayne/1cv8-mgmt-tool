import pytest

from conf import settings
from utils.postgres import POSTGRES_DEFAULT_PORT, POSTGRES_NAME, dbms_is_postgres, get_postgres_host_and_port, prepare_postgres_connection_vars


def test_dbms_is_postgres_returns_true_for_postgres():
    """
    `dbms_is_postgres` returns true for postgres dbms
    """
    assert dbms_is_postgres(POSTGRES_NAME)


def test_dbms_is_postgres_returns_false_for_non_postgres():
    """
    `dbms_is_postgres` returns false for non-postgres dbms
    """
    assert not dbms_is_postgres('MSSQL')


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


def test_prepare_postgres_connection_vars_raises_key_error_if_no_credentials_found():
    """
    `prepare_postgres_connection_vars` raises KeyError if credentials for user@host not found
    """
    with pytest.raises(KeyError):
        prepare_postgres_connection_vars('remotehost', 'postgres')


def test_prepare_postgres_connection_vars_returns_exactly_5_elements():
    """
    `prepare_postgres_connection_vars` returns db_host, db_port, db_pwd
    """
    result = prepare_postgres_connection_vars('localhost', 'postgres')
    assert len(result) == 3


def test_prepare_postgres_connection_vars_returns_correct_host():
    """
    `prepare_postgres_connection_vars` returns correct `db_host` value
    """
    host = 'localhost'
    result = prepare_postgres_connection_vars(host, 'postgres')
    assert result[0] == host


def test_prepare_postgres_connection_vars_returns_correct_port():
    """
    `prepare_postgres_connection_vars` returns correct `db_port` value
    """
    result = prepare_postgres_connection_vars('localhost', 'postgres')
    assert result[1] == POSTGRES_DEFAULT_PORT


def test_prepare_postgres_connection_vars_returns_correct_db_password():
    """
    `prepare_postgres_connection_vars` returns correct `db_pwd` value
    """
    host = 'localhost'
    db_user = 'postgres'
    result = prepare_postgres_connection_vars(host, db_user)
    assert result[2] == settings.PG_CREDENTIALS[f'{db_user}@{host}']
