from datetime import datetime, timedelta
import glob
import logging
import os
import _mssql
import settings
import subprocess

from core.cluster import ClusterControlInterface
from core.process import execute_v8_command, execute_in_threadpool
from core.common import get_platform_full_path, get_formatted_current_datetime, get_formatted_date, com_func_wrapper, \
    get_info_bases, get_info_base_credentials, get_server_address

server = get_server_address()
logPath = settings.LOG_PATH
logRetentionDays = settings.LOG_RETENTION_DAYS
backupPath = settings.BACKUP_PATH
backupReplicationEnabled = settings.BACKUP_REPLICATION_ENABLED
backupReplicationPaths = settings.BACKUP_REPLICATION_PATHS
backupRetentionDays = settings.BACKUP_RETENTION_DAYS


def remove_old_files_by_pattern(pattern, retention_days):
    """
    Удаляет файлы, дата изменения которых более чем <retention_days> назад
    :param pattern: паттерн пути и имени файлов для модуля glob https://docs.python.org/3/library/glob.html
    :param retention_days: определяет, насколько старые файлы будут удалены
    """
    files = glob.glob(pathname=pattern, recursive=False)
    ts = (datetime.now() - timedelta(days=retention_days)).timestamp()
    files_to_remove = [b for b in files if ts - os.path.getmtime(b) > 0]
    for f in files_to_remove:
        os.remove(f)


def _maintenance_info_base(ib_name):
    """
    1. Урезает журнал регистрации ИБ, оставляет данные только за последнюю неделю
    2. Удаляет старые резервные копии
    3. Удаляет старые log-файлы
    """
    logging.info(f'[{ib_name}] Start maintenance')
    result = True
    # Формирует команду для урезания журнала регистрации
    info_base_user, info_base_pwd = get_info_base_credentials(ib_name)
    time_str = get_formatted_current_datetime()
    ib_and_time_str = ib_name + '_' + time_str
    log_filename = os.path.join(logPath, f'{ib_and_time_str}.log')
    reduce_date = datetime.now() - timedelta(days=logRetentionDays)
    reduce_date_str = get_formatted_date(reduce_date)
    v8_command = \
        rf'"{get_platform_full_path()}" ' \
        rf'DESIGNER /S {server}\{ib_name} ' \
        rf'/N"{info_base_user}" /P"{info_base_pwd}" ' \
        rf'/Out {log_filename} -NoTruncate ' \
        rf'/ReduceEventLogSize {reduce_date_str}'
    execute_v8_command(
        ib_name, v8_command, log_filename, timeout=600
    )
    filename_pattern = "*" + ib_name + "_*.*"
    # Получает список резервных копий ИБ, удаляет старые
    logging.info(f'[{ib_name}] Removing backups older than {backupRetentionDays} days')
    path = backupPath + filename_pattern
    remove_old_files_by_pattern(path, backupRetentionDays)
    # Удаляет старые резервные копии в местах репликации
    if backupReplicationEnabled:
        for replication_path in backupReplicationPaths:
            path = replication_path + filename_pattern
            remove_old_files_by_pattern(path, backupRetentionDays)
    # Получает список log-файлов, удаляет старые
    logging.info(f'[{ib_name}] Removing logs older than {logRetentionDays} days')
    path = logPath + filename_pattern
    remove_old_files_by_pattern(path, logRetentionDays)
    return result


def _maintenance_vacuumdb(ib_name):
    logging.info(f'[{ib_name}] Start vacuumdb')
    cci = ClusterControlInterface()
    # Если соединение с рабочим процессом будет без данных для аутентификации в ИБ,
    # то не будет возможности получить данные, кроме имени ИБ
    wpc = cci.get_working_process_connection_with_info_base_auth()
    ib_info = cci.get_info_base(wpc, ib_name)
    if ib_info.DBMS.lower() != 'PostgreSQL'.lower():
        logging.error(f'[{ib_name}] vacuumdb can not be performed for {ib_info.DBMS} DBMS')
        return True
    db_user = ib_info.dbUser
    db_server = ib_info.dbServerName
    db_user_string = f'{db_user}@{db_server}'
    try:
        db_pwd = settings.PG_CREDENTIALS[db_user_string]
    except KeyError:
        logging.error(f'[{ib_name}] password not found for user {db_user_string}')
        return False
    db_name = ib_info.dbName
    time_str = get_formatted_current_datetime()
    ib_and_time_str = ib_name + '_' + time_str
    log_filename = os.path.join(logPath, f'{ib_and_time_str}.log')
    vacuumdb_command = \
        f'{settings.PG_VACUUMDB_PATH} --host={db_server} --port=5432 --username={db_user} ' \
        f'--analyze --verbose --dbname={db_name} > {log_filename} 2>&1'
    vacuumdb_env = os.environ.copy()
    vacuumdb_env['PGPASSWORD'] = db_pwd
    vacuumdb_process = subprocess.Popen(vacuumdb_command, env=vacuumdb_env, shell=True)
    logging.debug(f'[{ib_name}] vacuumdb PID is {str(vacuumdb_process.pid)}')
    vacuumdb_process.wait()
    if vacuumdb_process.returncode != 0:
        with open(log_filename) as log_file:
            read_data = log_file.read()
            # remove a trailing newline
            read_data = read_data.rstrip()
        logging.error(f'[{ib_name}] Log message <<< {read_data} >>>')
        return False
    logging.info(f'[{ib_name}] vacuumdb completed')
    return True


def _maintenance_adaptive_index_defrag(conn, ib_name, db_name):
    adaptive_index_defrag_exists = bool(conn.execute_scalar(
        'SELECT CASE WHEN OBJECT_ID(\'msdb.dbo.usp_AdaptiveIndexDefrag\') IS NOT NULL THEN 1 ELSE 0 END'
    ))
    if not adaptive_index_defrag_exists:
        server_net_addr = conn.execute_scalar('SELECT ConnectionProperty(\'local_net_address\')').decode('utf-8')
        logging.error(f'[{ib_name}] usp_AdaptiveIndexDefrag does not exists on server {server_net_addr}')
        return False
    usp_adaptive_index_defrag = conn.init_procedure('msdb.dbo.usp_AdaptiveIndexDefrag')
    #
    # @dbScope specifies a database name to defrag.
    # If not specified, all non-system databases plus msdb and model will be defragmented
    #
    usp_adaptive_index_defrag.bind(name='@dbScope', value=db_name, dbtype=_mssql.SQLVARCHAR)


def _maintenance_shrink_transaction_log(conn, ib_name, db_name):
    logging.info(f'[{ib_name}] Shrink database transaction log')
    conn.execute_query(
        "SELECT mf.name as log_file FROM sys.master_files mf "
        "inner join sys.databases d on mf.database_id = d.database_id "
        "where d.name = %(db_name)s and mf.type_desc = 'LOG'"
        , {'db_name': db_name}
    )
    log_files = [row for row in conn]
    if len(log_files) > 0:
        conn.execute_non_query('CHECKPOINT')
        for row in log_files:
            conn.execute_non_query(
                'DBCC SHRINKFILE (%(log_file)s, %(log_size)d) WITH NO_INFOMSGS',
                {'log_file': row['log_file'], 'log_size': settings.MSSQL_SHRINK_LOG_SIZE}
            )
    else:
        logging.warning(f'[{ib_name}] No log files found for database {db_name}')


def _maintenance_mssql_database(ib_name):
    logging.info(f'[{ib_name}] Start MSSQL database maintenance')
    with ClusterControlInterface() as cci:
        # Если соединение с рабочим процессом будет без данных для аутентификации в ИБ,
        # то не будет возможности получить данные, кроме имени ИБ
        wpc = cci.get_working_process_connection_with_info_base_auth()
        ib_info = cci.get_info_base(wpc, ib_name)
        if ib_info.DBMS.lower() != 'MSSQLServer'.lower():
            logging.error(f'[{ib_name}] MSSQL database maintenance can not be performed for {ib_info.DBMS} DBMS')
            return True
        db_user = ib_info.dbUser
        db_server = ib_info.dbServerName
        db_name = ib_info.dbName
    # Алиасы необходимы в случае, когда скрипт запускается из сетевого расположения, отличного от кластера 1С
    if db_server in settings.MSSQL_ALIASES:
        db_server = settings.MSSQL_ALIASES[db_server]
    db_user_string = db_user + '@' + db_server
    try:
        db_pwd = settings.MSSQL_CREDENTIALS[db_user_string]
    except KeyError:
        logging.error(f'[{ib_name}] password not found for user {db_user_string}')
        return False
    with _mssql.connect(server=db_server, user=db_user, password=db_pwd, database=db_name) as conn:
        _maintenance_shrink_transaction_log(conn, ib_name, db_name)
    return True


def concat_bool_to_result(result, bool_value):
    if type(bool_value) == bool:
        bool_in_result = result[1]
        bool_in_result = bool_in_result & bool_value
        return result[0], bool_in_result
    if type(bool_value) == tuple:
        return concat_bool_to_result(result, bool_value[1])


def maintenance_info_base(ib_name):
    result = ib_name, True
    try:
        if settings.V8_MAINTENANCE_ENABLED:
            result_v8 = com_func_wrapper(_maintenance_info_base, ib_name)
            result = concat_bool_to_result(result, result_v8)
        if settings.PG_MAINTENANCE_ENABLED:
            result_pg = _maintenance_vacuumdb(ib_name)
            result = concat_bool_to_result(result, result_pg)
        if settings.MSSQL_MAINTENANCE_ENABLED:
            result_ms = _maintenance_mssql_database(ib_name)
            result = concat_bool_to_result(result, result_ms)
        return result
    except Exception as e:
        logging.exception(f'[{ib_name}] Unknown exception occurred in thread')
        return ib_name, False


if __name__ == "__main__":
    try:
        info_bases = get_info_bases()
        maintenanceThreads = settings.MAINTENANCE_THREADS
        execute_in_threadpool(maintenance_info_base, info_bases, maintenanceThreads)
        logging.info('Done')
    except Exception as e:
        logging.exception('Unknown exception occured in main thread')
