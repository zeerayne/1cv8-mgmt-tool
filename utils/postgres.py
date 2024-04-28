from typing import Tuple

import asyncpg

from conf import settings

POSTGRES_DEFAULT_PORT = "5432"
POSTGRES_NAME = "PostgreSQL"


def dbms_is_postgres(dbms: str) -> bool:
    return dbms.lower() == POSTGRES_NAME.lower()


def get_postgres_host_and_port(db_server_string: str) -> Tuple[str, str]:
    db_host = db_server_string.split(":")[0]
    try:
        db_port = db_server_string.split(":")[1]
    except IndexError:
        db_port = POSTGRES_DEFAULT_PORT
    return db_host, db_port


def prepare_postgres_connection_vars(db_server: str, db_user: str) -> Tuple[str, str, str]:
    db_user_string = f"{db_user}@{db_server}"
    db_host, db_port = get_postgres_host_and_port(db_server)
    try:
        db_pwd = settings.PG_CREDENTIALS[db_user_string]
    except KeyError:
        raise KeyError(f"{POSTGRES_NAME} password not found for user {db_user_string}")
    return db_host, db_port, db_pwd


async def get_postgres_version(
    db_host: str, db_port: str, db_name: str, db_user: str, db_pwd: str
) -> asyncpg.types.ServerVersion:
    pg_con = await asyncpg.connect(host=db_host, port=db_port, database=db_name, user=db_user, password=db_pwd)
    pg_version = pg_con.get_server_version()
    await pg_con.close()
    return pg_version
