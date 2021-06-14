import concurrent.futures
import logging
import os
import pathlib
import settings
import subprocess
import sys
from datetime import datetime
from shutil import copyfile
import core.common as common_funcs
from core.cluster import ClusterControlInterface
from core.exceptions import V8Exception
from core.process import execute_v8_command
from core.aws import analyze_s3_result, upload_infobase_to_s3
from core.process import pycom_threadpool_initializer
from util.notification import make_html_table, send_notification

server = common_funcs.get_server_address()
backupPath = settings.BACKUP_PATH
backupReplicationEnabled = settings.BACKUP_REPLICATION_ENABLED
backupReplicationPaths = settings.BACKUP_REPLICATION_PATHS
logPath = settings.LOG_PATH


def replicate_backup(backup_fullpath, replication_paths):
    backup_filename = common_funcs.path_leaf(backup_fullpath)
    for path in replication_paths:
        try:
            pathlib.Path(path).mkdir(parents=True, exist_ok=True)
            replication_fullpath = path + backup_filename
            logging.info(f'Replicating {backup_fullpath} to {replication_fullpath}')
            copyfile(backup_fullpath, replication_fullpath)
        except Exception as e:
            logging.exception(f'Problems while replicating to {path}: {e}')


def _backup_info_base(ib_name):
    """
    1. Блокирует фоновые задания и новые сеансы
    2. Принудительно завершает текущие сеансы
    3. Выгружает информационную базу в *.dt файл
    4. Снимает блокировку фоновых заданий и сеансов

    ?. Надо предусмотреть, что на ночь могут запускать групповое перепроведение, которое прерывать
    нельзя. Поскольку в бух 3.0 оно выполняется в фоновом задании, то определить его можно по наличию
    активного фонового задания с названием "Групповое перепроведение документов".

    ?. Проверить, как будет работать получение InfoBaseInfo, если подключились к отключенному рабочему
    процессу. Возможно придется перебирать рабочие процессы в поисках активного.

    ?. Посмотреть как будет работать, если база в монопольном режиме.
    """
    logging.info(f'[{ib_name}] Start backup')
    # Код блокировки новых сеансов
    permission_code = "0000"
    # Формирует команду для выгрузки
    info_base_user, info_base_pwd = common_funcs.get_info_base_credentials(ib_name)
    ib_and_time_str = common_funcs.get_ib_and_time_string(ib_name)
    dt_filename = os.path.join(backupPath, common_funcs.append_file_extension_to_string(ib_and_time_str, 'dt'))
    log_filename = os.path.join(logPath, common_funcs.append_file_extension_to_string(ib_and_time_str, 'log'))
    # https://its.1c.ru/db/v838doc#bookmark:adm:TI000000526
    v8_command = \
        rf'"{common_funcs.get_platform_full_path()}" ' \
        rf'DESIGNER /S {server}\{ib_name} ' \
        rf'/N"{info_base_user}" /P"{info_base_pwd}" ' \
        rf'/Out {log_filename} -NoTruncate ' \
        rf'/UC "{permission_code}" ' \
        rf'/DumpIB {dt_filename}'
    logging.info(f'[{ib_name}] Created dump command [{v8_command}]')
    # Выгружает информационную базу в *.dt файл
    backup_retries = settings.BACKUP_RETRIES
    # Добавляем 1 к количеству повторных попыток, потому что одну попытку всегда нужно делать
    for i in range(0, backup_retries + 1):
        try:
            execute_v8_command(
                ib_name, v8_command, log_filename, permission_code, 1200
            )
            break
        except V8Exception as e:
            # Если количество попыток исчерпано, но ошибка по прежнему присутствует
            if i == backup_retries:
                raise e
            else:
                logging.debug(f'[{ib_name}] Backup failed, retrying')
    return dt_filename


def _backup_pgdump(ib_name):
    """
    Выполняет резервное копирование ИБ средствами СУБД PostgreSQL при помощи утилиты pg_dump
    1. Проверяет, использует ли ИБ СУБД PostgreSQL
    2. Проверяет, есть ли подходящие учетные данные для подключения к базе данных
    3. Создаёт резервную копию средствами pg_dump
    :param ib_name:
    :return:
    """
    logging.info(f'[{ib_name}] Start pgdump')
    with ClusterControlInterface() as cci:
        # Если соединение с рабочим процессом будет без данных для аутентификации в ИБ,
        # то не будет возможности получить данные, кроме имени ИБ
        wpc = cci.get_working_process_connection_with_info_base_auth()
        ib_info = cci.get_info_base(wpc, ib_name)
        if ib_info.DBMS.lower() != 'PostgreSQL'.lower():
            logging.error(f'[{ib_name}] pgdump can not be performed for {ib_info.DBMS} DBMS')
            return False
        db_user = ib_info.dbUser
        db_server = ib_info.dbServerName
        db_user_string = db_user + '@' + db_server
        try:
            db_pwd = settings.PG_CREDENTIALS[db_user_string]
        except KeyError:
            logging.error(f'[{ib_name}] password not found for user {db_user_string}')
            return False
        db_name = ib_info.dbName
    ib_and_time_str = common_funcs.get_ib_and_time_string(ib_name)
    backup_filename = os.path.join(backupPath, common_funcs.append_file_extension_to_string(ib_and_time_str, 'pgdump'))
    log_filename = os.path.join(logPath, common_funcs.append_file_extension_to_string(ib_and_time_str, 'log'))
    # --blobs
    # Include large objects in the dump.
    # This is the default behavior except when --schema, --table, or --schema-only is specified.
    #
    # --format=custom
    # Output a custom-format archive suitable for input into pg_restore.
    # Together with the directory output format, this is the most flexible output format in that it allows
    # manual selection and reordering of archived items during restore. This format is also compressed by default.
    pgdump_command = \
        rf'{settings.PG_DUMP_PATH} ' \
        rf'--host={db_server} --port=5432 --username={db_user} ' \
        rf'--format=custom --blobs --verbose ' \
        rf'--file={backup_filename} --dbname={db_name} > {log_filename} 2>&1'
    pgdump_env = os.environ.copy()
    pgdump_env['PGPASSWORD'] = db_pwd
    pgdump_process = subprocess.Popen(pgdump_command, env=pgdump_env, shell=True)
    logging.debug(f'[{ib_name}] pg_dump PID is {str(pgdump_process.pid)}')
    pgdump_process.wait()
    if pgdump_process.returncode != 0:
        with open(log_filename) as log_file:
            read_data = log_file.read()
            # remove a trailing newline
            read_data = read_data.rstrip()
        logging.error(f'[{ib_name}] Log message <<< {read_data} >>>')
        return False
    logging.info(f'[{ib_name}] pg_dump completed')
    return backup_filename


def backup_info_base(ib_name):
    try:
        if settings.PG_BACKUP_ENABLED:
            result = ib_name, _backup_pgdump(ib_name)
        else:
            result = common_funcs.com_func_wrapper(_backup_info_base, ib_name)
        # Если включена репликация и результат выгрузки успешен
        if backupReplicationEnabled and result and result[1]:
            backup_filename = result[0]
            # Копирует файл бэкапа в дополнительные места
            replicate_backup(backup_filename, backupReplicationPaths)
        return result
    except Exception as e:
        logging.exception(f'[{ib_name}] Unknown exception occurred in thread')
        return ib_name, False


def analyze_backup_result(result, workload, datetime_start, datetime_finish):
    succeeded = 0
    failed = 0
    for e in result:
        if e[1]:
            succeeded += 1
        else:
            failed += 1
            logging.error(f'[{e[0]}] FAILED')
    diff = (datetime_finish - datetime_start).total_seconds()
    logging.info(f'[Backup] {succeeded} succeeded; {failed} failed; Avg. time {diff / len(result):.1f}s.')
    if len(result) != len(workload):
        processed_info_bases = [e[0] for e in result]
        missed = 0
        for w in workload:
            if w not in processed_info_bases:
                logging.warning(f'[{w}] MISSED')
                missed += 1
        logging.warning(f'[Backup] {len(workload)} required; {len(result)} done; {missed} missed')


def main():
    MIN_PYTHON_VERSION = (3, 7)
    if sys.version_info < MIN_PYTHON_VERSION:
        sys.exit("Python %s.%s or later is required.\n" % MIN_PYTHON_VERSION)
    try:
        # Если скрипт используется через планировщик задач windows, лучше всего логгировать консольный вывод в файл
        # Например: backup.py >> D:\backup\log\1cv8-mgmt-backup-system.log 2>&1
        info_bases = common_funcs.get_info_bases()
        backup_threads = settings.BACKUP_THREADS
        aws_threads = settings.AWS_THREADS
        backup_result = []
        aws_result = []
        with concurrent.futures.ProcessPoolExecutor(
                max_workers=backup_threads,
                #thread_name_prefix='BackupThread',
                initializer=pycom_threadpool_initializer
            ) as backup_executor, \
            concurrent.futures.ProcessPoolExecutor(
                max_workers=aws_threads,
                #thread_name_prefix='AWSThread'
            ) as aws_executor:
            logging.info(f'[Backup] Thread pool executors initialized: {backup_threads} backup thread, {aws_threads} AWS threads')
            backup_futures = []
            backup_datetime_start = datetime.now()
            for ib_name in info_bases:
                backup_futures.append(
                    backup_executor.submit(backup_info_base, ib_name)
                )
            aws_futures = []
            aws_datetime_start = None
            for future in concurrent.futures.as_completed(backup_futures):
                if not aws_datetime_start:
                    aws_datetime_start = datetime.now()
                try:
                    e = future.result()
                    backup_result.append(e)
                    # Только резервные копии, созданные без ошибок нужно загрузить на S3
                    if e[1] and settings.AWS_ENABLED:
                        aws_futures.append(
                            aws_executor.submit(upload_infobase_to_s3, e[0], e[1])
                        )
                except concurrent.futures.process.BrokenProcessPool:
                    logging.error('Got BrokenProcessPool exception')
            # при работе с большим количеством COM-объектов процессы питона крашатся, 
            # часть резервных копий может быть не сделана, требуется пересоздать ProcessPoolExecutor
            if len(backup_result) != len(info_bases):
                logging.warning('[Backup] Backup process pool had crashed, retrying')
                processed_info_bases = [e[0] for e in backup_result]
                missed = []
                for w in info_bases:
                    if w not in processed_info_bases:
                        missed.append(w)
                with concurrent.futures.ProcessPoolExecutor(
                    max_workers=backup_threads,
                    initializer=pycom_threadpool_initializer
                ) as fallback_backup_executor:
                    logging.info(f'[Backup] Thread pool executors initialized: {backup_threads} backup thread')
                    backup_futures = []
                    for ib_name in missed:
                        backup_futures.append(
                            fallback_backup_executor.submit(backup_info_base, ib_name)
                        )
                    for future in concurrent.futures.as_completed(backup_futures):
                        if not aws_datetime_start:
                            aws_datetime_start = datetime.now()
                        try:
                            e = future.result()
                            backup_result.append(e)
                            # Только резервные копии, созданные без ошибок нужно загрузить на S3
                            if e[1] and settings.AWS_ENABLED:
                                aws_futures.append(
                                    aws_executor.submit(upload_infobase_to_s3, e[0], e[1])
                                )
                        except concurrent.futures.process.BrokenProcessPool:
                            logging.error('Got BrokenProcessPool exception')
            backup_datetime_finish = datetime.now()
            for future in concurrent.futures.as_completed(aws_futures):
                e = future.result()
                aws_result.append(e)
            aws_datetime_finish = datetime.now()
        analyze_backup_result(backup_result, info_bases, backup_datetime_start, backup_datetime_finish)
        if settings.AWS_ENABLED:
            analyze_s3_result(aws_result, info_bases, aws_datetime_start, aws_datetime_finish)

        if settings.EMAIL_NOTIFY_ENABLED:
            logging.info('Sending email notification')
            msg = ''
            msg += make_html_table('Backup', backup_result)
            if settings.AWS_ENABLED:
                msg += make_html_table('AWS upload', aws_result)
            send_notification('1cv8-mgmt backup', msg)

        logging.info('Done')
    except Exception as e:
        logging.exception('Unknown exception occurred in main thread')


if __name__ == "__main__":
    main()
