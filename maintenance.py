from datetime import datetime, timedelta
import glob
import logging
import os
import settings
import subprocess

import core.common as common_funcs

from core.cluster import ClusterControlInterface
from core.process import execute_v8_command, execute_in_threadpool


server = common_funcs.get_server_address()
logPath = settings.LOG_PATH
logRetentionDays = settings.LOG_RETENTION_DAYS
backupPath = settings.BACKUP_PATH
backupReplicationEnabled = settings.BACKUP_REPLICATION_ENABLED
backupReplicationPaths = settings.BACKUP_REPLICATION_PATHS
backupRetentionDays = settings.BACKUP_RETENTION_DAYS


log = logging.getLogger(__name__)
log_prefix = 'Maintenance'


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
    log.info(f'<{ib_name}> Start maintenance')
    result = True
    # Формирует команду для урезания журнала регистрации
    info_base_user, info_base_pwd = common_funcs.get_info_base_credentials(ib_name)
    log_filename = os.path.join(logPath, common_funcs.get_ib_and_time_filename(ib_name, 'log'))
    reduce_date = datetime.now() - timedelta(days=logRetentionDays)
    reduce_date_str = common_funcs.get_formatted_date(reduce_date)
    v8_command = \
        rf'"{common_funcs.get_platform_full_path()}" ' \
        rf'DESIGNER /S {server}\{ib_name} ' \
        rf'/N"{info_base_user}" /P"{info_base_pwd}" ' \
        rf'/Out {log_filename} -NoTruncate ' \
        rf'/ReduceEventLogSize {reduce_date_str}'
    execute_v8_command(
        ib_name, v8_command, log_filename, timeout=600
    )
    filename_pattern = f'*{ib_name}_*.*'
    # Получает список резервных копий ИБ, удаляет старые
    log.info(f'<{ib_name}> Removing backups older than {backupRetentionDays} days')
    path = os.path.join(backupPath, filename_pattern)
    remove_old_files_by_pattern(path, backupRetentionDays)
    # Удаляет старые резервные копии в местах репликации
    if backupReplicationEnabled:
        for replication_path in backupReplicationPaths:
            path = os.path.join(replication_path, filename_pattern)
            remove_old_files_by_pattern(path, backupRetentionDays)
    # Получает список log-файлов, удаляет старые
    log.info(f'<{ib_name}> Removing logs older than {logRetentionDays} days')
    path = os.path.join(logPath, filename_pattern)
    remove_old_files_by_pattern(path, logRetentionDays)
    return result


def _maintenance_vacuumdb(ib_name):
    log.info(f'<{ib_name}> Start vacuumdb')
    cci = ClusterControlInterface()
    # Если соединение с рабочим процессом будет без данных для аутентификации в ИБ,
    # то не будет возможности получить данные, кроме имени ИБ
    wpc = cci.get_working_process_connection_with_info_base_auth()
    ib_info = cci.get_info_base(wpc, ib_name)
    if ib_info.DBMS.lower() != 'PostgreSQL'.lower():
        log.error(f'<{ib_name}> vacuumdb can not be performed for {ib_info.DBMS} DBMS')
        return True
    db_user = ib_info.dbUser
    db_server = ib_info.dbServerName
    db_user_string = f'{db_user}@{db_server}'
    try:
        db_pwd = settings.PG_CREDENTIALS[db_user_string]
    except KeyError:
        log.error(f'<{ib_name}> password not found for user {db_user_string}')
        return False
    db_name = ib_info.dbName
    log_filename = os.path.join(logPath, common_funcs.get_ib_and_time_filename(ib_name, 'log'))
    vacuumdb_command = \
        f'{settings.PG_VACUUMDB_PATH} --host={db_server} --port=5432 --username={db_user} ' \
        f'--analyze --verbose --dbname={db_name} > {log_filename} 2>&1'
    vacuumdb_env = os.environ.copy()
    vacuumdb_env['PGPASSWORD'] = db_pwd
    vacuumdb_process = subprocess.Popen(vacuumdb_command, env=vacuumdb_env, shell=True)
    log.debug(f'<{ib_name}> vacuumdb PID is {str(vacuumdb_process.pid)}')
    vacuumdb_process.wait()
    if vacuumdb_process.returncode != 0:
        log_file_content = common_funcs.read_file_content(log_filename)
        log.error(f'<{ib_name}> Log message :: {log_file_content}')
        return False
    log.info(f'<{ib_name}> vacuumdb completed')
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
            result_v8 = common_funcs.com_func_wrapper(_maintenance_info_base, ib_name)
            result = concat_bool_to_result(result, result_v8)
        if settings.PG_MAINTENANCE_ENABLED:
            result_pg = _maintenance_vacuumdb(ib_name)
            result = concat_bool_to_result(result, result_pg)
        return result
    except Exception as e:
        log.exception(f'<{ib_name}> Unknown exception occurred in thread')
        return ib_name, False


def main():
    try:
        info_bases = common_funcs.get_info_bases()
        maintenanceThreads = settings.MAINTENANCE_THREADS
        execute_in_threadpool(maintenance_info_base, info_bases, maintenanceThreads)
        log.info(f'<{log_prefix}> Done')
    except Exception as e:
        log.exception(f'<{log_prefix}> Unknown exception occured in main thread')


if __name__ == "__main__":
    main()
