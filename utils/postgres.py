from typing import Tuple


POSTGRES_DEFAULT_PORT = '5432'


def get_postgres_host_and_port(db_server_string: str) -> Tuple[str, str]:
    db_host = db_server_string.split(':')[0]
    try:
        db_port = db_server_string.split(':')[1]
    except IndexError:
        db_port = POSTGRES_DEFAULT_PORT
    return db_host, db_port
