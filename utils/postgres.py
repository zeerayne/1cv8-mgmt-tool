from typing import Tuple

from conf import settings


POSTGRES_DEFAULT_PORT = '5432'
POSTGRES_NAME = 'PostgreSQL'


def dbms_is_postgres(dbms: str) -> bool:
    return dbms.lower() == POSTGRES_NAME.lower()


def get_postgres_host_and_port(db_server_string: str) -> Tuple[str, str]:
    db_host = db_server_string.split(':')[0]
    try:
        db_port = db_server_string.split(':')[1]
    except IndexError:
        db_port = POSTGRES_DEFAULT_PORT
    return db_host, db_port


def prepare_postgres_connection_vars(db_server: str, db_user: str) -> Tuple[str, str, str]:
    db_user_string = f'{db_user}@{db_server}'
    db_host, db_port = get_postgres_host_and_port(db_server)
    try:
        db_pwd = settings.PG_CREDENTIALS[db_user_string]
    except KeyError:
        raise KeyError(f'{POSTGRES_NAME} password not found for user {db_user_string}')
    return db_host, db_port, db_pwd
