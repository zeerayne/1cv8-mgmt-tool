import asyncio
import logging
import os
import pathlib
import sys
from datetime import datetime
from typing import List

import aioshutil

import core.models as core_models
from conf import settings
from core import utils
from core.analyze import analyze_backup_result, analyze_s3_result
from core.aws import upload_infobase_to_s3
from core.cluster import utils as cluster_utils
from core.exceptions import SubprocessException, V8Exception
from core.process import execute_subprocess_command, execute_v8_command
from utils import postgres
from utils.log import configure_logging
from utils.notification import make_html_table, send_notification

log = logging.getLogger(__name__)
log_prefix = "Backup"


async def replicate_backup(backup_fullpath: str, replication_paths: List[str]):
    backup_filename = utils.path_leaf(backup_fullpath)
    for path in replication_paths:
        try:
            pathlib.Path(path).mkdir(parents=True, exist_ok=True)
            replication_fullpath = os.path.join(path, backup_filename)
            log.info(f"Replicating {backup_fullpath} to {replication_fullpath}")
            await aioshutil.copyfile(backup_fullpath, replication_fullpath)
        except Exception as e:
            log.exception(f"Problems while replicating to {path}: {e}")


async def rotate_backups(ib_name):
    backup_retention_days = settings.BACKUP_RETENTION_DAYS
    filename_pattern = utils.get_infobase_glob_pattern(ib_name)
    rotate_paths = [settings.BACKUP_PATH]
    if settings.BACKUP_REPLICATION:
        rotate_paths += settings.BACKUP_REPLICATION_PATHS
    # Удаляет старые резервные копии
    for rotation_path in rotate_paths:
        log.info(f"<{ib_name}> Removing backups older than {backup_retention_days} days from {rotation_path}")
        path = os.path.join(rotation_path, filename_pattern)
        await utils.remove_old_files_by_pattern(path, backup_retention_days)


async def _backup_v8(ib_name: str, *args, **kwargs) -> core_models.InfoBaseBackupTaskResult:
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
    log.info(f"<{ib_name}> Start backup")
    # Код блокировки новых сеансов
    permission_code = settings.V8_PERMISSION_CODE
    # Формирует команду для выгрузки
    info_base_user, info_base_pwd = utils.get_info_base_credentials(ib_name)
    ib_and_time_str = utils.get_ib_and_time_string(ib_name)
    dt_filename = os.path.join(settings.BACKUP_PATH, utils.append_file_extension_to_string(ib_and_time_str, "dt"))
    log_filename = os.path.join(settings.LOG_PATH, utils.append_file_extension_to_string(ib_and_time_str, "log"))
    # https://its.1c.ru/db/v838doc#bookmark:adm:TI000000526
    v8_command = (
        rf'"{utils.get_platform_full_path()}" '
        rf"DESIGNER /S {cluster_utils.get_server_agent_address()}\{ib_name} "
        rf'/N"{info_base_user}" /P"{info_base_pwd}" '
        rf"/Out {log_filename} -NoTruncate "
        rf'/UC "{permission_code}" '
        rf"/DumpIB {dt_filename}"
    )
    log.debug(f"<{ib_name}> Created dump command [{v8_command}]")
    # Выгружает информационную базу в *.dt файл
    backup_retries = settings.BACKUP_RETRIES_V8
    # Добавляет 1 к количеству повторных попыток, потому что одну попытку всегда нужно делать
    for i in range(0, backup_retries + 1):
        try:
            await execute_v8_command(
                ib_name,
                v8_command,
                log_filename,
                permission_code,
                timeout=settings.BACKUP_TIMEOUT_V8,
                log_output_on_success=True,
            )
            break
        except V8Exception:
            # Если количество попыток исчерпано, но ошибка по прежнему присутствует
            if i == backup_retries:
                log.exception(f"<{ib_name}> Backup failed, retries exceeded")
                return core_models.InfoBaseBackupTaskResult(ib_name, False)
            else:
                log.exception(f"<{ib_name}> Backup failed, retrying")
    return core_models.InfoBaseBackupTaskResult(ib_name, True, dt_filename)


async def _backup_pgdump(
    ib_name: str, db_server: str, db_name: str, db_user: str, *args, **kwargs
) -> core_models.InfoBaseBackupTaskResult:
    """
    Выполняет резервное копирование ИБ средствами СУБД PostgreSQL при помощи утилиты pg_dump
    1. Проверяет, использует ли ИБ СУБД PostgreSQL
    2. Проверяет, есть ли подходящие учетные данные для подключения к базе данных
    3. Создаёт резервную копию средствами pg_dump
    :param ib_name:
    :return:
    """
    log.info(f"<{ib_name}> Start pgdump")
    try:
        db_host, db_port, db_pwd = postgres.prepare_postgres_connection_vars(db_server, db_user)
    except (ValueError, KeyError) as e:
        log.error(f"<{ib_name}> {str(e)}")
        return core_models.InfoBaseBackupTaskResult(ib_name, False)
    ib_and_time_str = utils.get_ib_and_time_string(ib_name)
    backup_filename = os.path.join(
        settings.BACKUP_PATH, utils.append_file_extension_to_string(ib_and_time_str, "pgdump")
    )
    log_filename = os.path.join(settings.LOG_PATH, utils.append_file_extension_to_string(ib_and_time_str, "log"))
    pg_dump_path = os.path.join(settings.PG_BIN_PATH, "pg_dump.exe")
    # --blobs
    # Include large objects in the dump.
    # This is the default behavior except when --schema, --table, or --schema-only is specified.
    #
    # --format=custom
    # Output a custom-format archive suitable for input into pg_restore.
    # Together with the directory output format, this is the most flexible output format in that it allows
    # manual selection and reordering of archived items during restore. This format is also compressed by default.
    pgdump_command = (
        rf'"{pg_dump_path}" '
        rf"--host={db_host} --port={db_port} --username={db_user} "
        rf"--format=custom --blobs --verbose "
        rf"--file={backup_filename} --dbname={db_name} > {log_filename} 2>&1"
    )
    pgdump_env = os.environ.copy()
    pgdump_env["PGPASSWORD"] = db_pwd
    log.debug(f"<{ib_name}> Created pgdump command [{pgdump_command}]")
    # Делает резервную копию базы данных в *.pgdump файл
    backup_retries = settings.BACKUP_RETRIES_PG
    # Добавляет 1 к количеству повторных попыток, потому что одну попытку всегда нужно делать
    for i in range(0, backup_retries + 1):
        try:
            await execute_subprocess_command(ib_name, pgdump_command, log_filename, env=pgdump_env)
            break
        except SubprocessException:
            # Если количество попыток исчерпано, но ошибка по прежнему присутствует
            if i == backup_retries:
                log.exception(f"<{ib_name}> Backup failed, retries exceeded")
                return core_models.InfoBaseBackupTaskResult(ib_name, False)
            else:
                log.exception(f"<{ib_name}> Backup failed, retrying")
    return core_models.InfoBaseBackupTaskResult(ib_name, True, backup_filename)


async def _backup_info_base(ib_name: str) -> core_models.InfoBaseBackupTaskResult:
    cci = cluster_utils.get_cluster_controller_class()()
    ib_info = cci.get_info_base(ib_name)
    db_server = ib_info.dbServerName
    dbms = ib_info.DBMS
    db_name = ib_info.dbName
    db_user = ib_info.dbUser
    if settings.BACKUP_PG and postgres.dbms_is_postgres(dbms):
        result = await _backup_pgdump(ib_name, db_server, db_name, db_user)
    else:
        result = await cluster_utils.com_func_wrapper(_backup_v8, ib_name)
    return result


async def backup_info_base(ib_name: str, semaphore: asyncio.Semaphore) -> core_models.InfoBaseBackupTaskResult:
    async with semaphore:
        try:
            result = await _backup_info_base(ib_name)
        except Exception:
            log.exception(f"<{ib_name}> Unknown exception occurred in `_backup_info_base` coroutine")
            return core_models.InfoBaseBackupTaskResult(ib_name, False)
        try:
            # Если включена репликация и результат бэкапа успешен
            if settings.BACKUP_REPLICATION and result.succeeded:
                await replicate_backup(result.backup_filename, settings.BACKUP_REPLICATION_PATHS)
        except Exception:
            log.exception(f"<{ib_name}> Unknown exception occurred in `replicate_backup` coroutine")
        try:
            # Ротация бэкапов, удаляет старые
            await rotate_backups(ib_name)
        except Exception:
            log.exception(f"<{ib_name}> Unknown exception occurred in `rotate_backups` coroutine")
        return result


def analyze_results(
    infobases: List[str],
    backup_result: List[core_models.InfoBaseBackupTaskResult],
    backup_datetime_start: datetime,
    backup_datetime_finish: datetime,
    aws_result: List[core_models.InfoBaseAWSUploadTaskResult],
    aws_datetime_start: datetime,
    aws_datetime_finish: datetime,
):
    analyze_backup_result(backup_result, infobases, backup_datetime_start, backup_datetime_finish)
    if settings.AWS_ENABLED:
        analyze_s3_result(aws_result, infobases, aws_datetime_start, aws_datetime_finish)


def send_email_notification(
    backup_result: List[core_models.InfoBaseBackupTaskResult], aws_result: List[core_models.InfoBaseAWSUploadTaskResult]
):
    if settings.NOTIFY_EMAIL_ENABLED:
        log.info(f"<{log_prefix}> Sending email notification")
        msg = ""
        msg += make_html_table("Backup", backup_result)
        if settings.AWS_ENABLED:
            msg += make_html_table("AWS upload", aws_result)
        send_notification(settings.NOTIFY_EMAIL_CAPTION, msg)


async def main():
    try:
        # Если скрипт используется через планировщик задач windows, лучше всего логгировать консольный вывод в файл
        # Например: backup.py >> D:\backup\log\1cv8-mgmt-backup-system.log 2>&1
        cci = cluster_utils.get_cluster_controller_class()()
        info_bases = cci.get_info_bases()
        backup_concurrency = settings.BACKUP_CONCURRENCY
        aws_concurrency = settings.AWS_CONCURRENCY
        backup_results = []
        aws_results = []

        backup_semaphore = asyncio.Semaphore(backup_concurrency)
        aws_semaphore = asyncio.Semaphore(aws_concurrency)
        log.info(
            f"<{log_prefix}> Asyncio semaphores initialized: {backup_concurrency} backup concurrency, {aws_concurrency} AWS concurrency"
        )
        backup_coroutines = [backup_info_base(ib_name, backup_semaphore) for ib_name in info_bases]
        backup_datetime_start = datetime.now()
        aws_tasks = []
        aws_datetime_start = None
        for backup_coro in asyncio.as_completed(backup_coroutines):
            backup_result = await backup_coro
            backup_results.append(backup_result)
            backup_datetime_finish = datetime.now()
            # Только резервные копии, созданные без ошибок нужно загрузить на S3
            if backup_result.succeeded and settings.AWS_ENABLED:
                if aws_datetime_start is None:
                    aws_datetime_start = datetime.now()
                aws_tasks.append(
                    asyncio.create_task(
                        upload_infobase_to_s3(
                            backup_result.infobase_name, backup_result.backup_filename, aws_semaphore
                        ),
                        name=f"Task :: Upload {backup_result.infobase_name} to S3",
                    )
                )

        if aws_tasks:
            await asyncio.wait(aws_tasks)
            aws_results = [task.result() for task in aws_tasks]
        aws_datetime_finish = datetime.now()

        analyze_results(
            info_bases,
            backup_results,
            backup_datetime_start,
            backup_datetime_finish,
            aws_results,
            aws_datetime_start,
            aws_datetime_finish,
        )

        send_email_notification(backup_results, aws_results)

        log.info(f"<{log_prefix}> Done")
    except Exception:
        log.exception(f"<{log_prefix}> Unknown exception occurred in main coroutine")


if __name__ == "__main__":
    configure_logging(settings.LOG_LEVEL)
    if sys.version_info < (3, 10):
        # Использование asyncio.run() в windows бросает исключение
        # `RuntimeError: Event loop is closed` при завершении run.
        # WindowsSelectorEventLoopPolicy не работает с подпроцессами полноценно в python 3.8
        asyncio.get_event_loop().run_until_complete(main())
    else:
        asyncio.run(main())
