import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import List

import core.models as core_models
from conf import settings
from core import utils
from core.analyze import analyze_maintenance_result
from core.cluster import utils as cluster_utils
from core.exceptions import SubprocessException, V8Exception
from core import process
from utils import postgres
from utils.asyncio import initialize_event_loop, initialize_semaphore
from utils.log import configure_logging

log = logging.getLogger(__name__)
log_prefix = "Maintenance"


async def rotate_logs(ib_name):
    logRetentionDays = settings.MAINTENANCE_LOG_RETENTION_DAYS
    filename_pattern = utils.get_infobase_glob_pattern(ib_name, "log")
    # Получает список log-файлов, удаляет старые
    log.info(f"<{ib_name}> Removing logs older than {logRetentionDays} days")
    path = os.path.join(settings.LOG_PATH, filename_pattern)
    await utils.remove_old_files_by_pattern(path, logRetentionDays)
    return core_models.InfoBaseMaintenanceTaskResult(ib_name, True)


async def _maintenance_v8(ib_name: str, *args, **kwargs) -> core_models.InfoBaseMaintenanceTaskResult:
    """
    1. Урезает журнал регистрации ИБ, оставляет данные только за последнюю неделю
    2. Удаляет старые резервные копии
    3. Удаляет старые log-файлы
    """
    log.info(f"<{ib_name}> Start 1cv8 maintenance")
    log_filename = os.path.join(settings.LOG_PATH, utils.get_ib_and_time_filename(ib_name, "log"))
    reduce_date = datetime.now() - timedelta(days=settings.MAINTENANCE_REGISTRATION_LOG_RETENTION_DAYS)
    v8_command = utils.assemble_maintenance_v8_command(ib_name, reduce_date, log_filename)
    try:
        await process.execute_v8_command_wrapper(
            ib_name, v8_command, log_filename, timeout=settings.MAINTENANCE_TIMEOUT_V8, log_output_on_success=True
        )
    except V8Exception:
        return core_models.InfoBaseMaintenanceTaskResult(ib_name, False)
    return core_models.InfoBaseMaintenanceTaskResult(ib_name, True)


async def _maintenance_vacuumdb(
    ib_name: str, db_server: str, db_name: str, db_user: str, *args, **kwargs
) -> core_models.InfoBaseMaintenanceTaskResult:
    log.info(f"<{ib_name}> Start vacuumdb")
    try:
        db_host, db_port, db_pwd = postgres.prepare_postgres_connection_vars(db_server, db_user)
    except KeyError as e:
        log.error(f"<{ib_name}> {str(e)}")
        return core_models.InfoBaseMaintenanceTaskResult(ib_name, False)
    log_filename = os.path.join(settings.LOG_PATH, utils.get_ib_and_time_filename(ib_name, "log"))
    pg_vacuumdb_path = os.path.join(settings.PG_BIN_PATH, "vacuumdb.exe")
    vacuumdb_command = (
        f'"{pg_vacuumdb_path}" --host={db_host} --port={db_port} --username={db_user} '
        f"--analyze --verbose --dbname={db_name} > {log_filename} 2>&1"
    )
    vacuumdb_env = os.environ.copy()
    vacuumdb_env["PGPASSWORD"] = db_pwd
    try:
        await process.execute_subprocess_command(ib_name, vacuumdb_command, log_filename, env=vacuumdb_env)
    except SubprocessException:
        return core_models.InfoBaseMaintenanceTaskResult(ib_name, False)
    return core_models.InfoBaseMaintenanceTaskResult(ib_name, True)


async def maintenance_info_base(
    ib_name: str, semaphore: asyncio.Semaphore
) -> core_models.InfoBaseMaintenanceTaskResult:
    async with semaphore:
        try:
            if utils.infobase_is_in_cluster(ib_name):
                cci = cluster_utils.get_cluster_controller_class()()
                ib_info = cci.get_info_base(ib_name)
                db_server = ib_info.dbServerName
                dbms = ib_info.DBMS
                db_name = ib_info.dbName
                db_user = ib_info.dbUser
                succeeded = True
                if settings.MAINTENANCE_V8:
                    result_v8 = await cluster_utils.com_func_wrapper(_maintenance_v8, ib_name)
                    succeeded &= result_v8.succeeded
                if settings.MAINTENANCE_PG and postgres.dbms_is_postgres(dbms):
                    result_pg = await _maintenance_vacuumdb(ib_name, db_server, db_name, db_user)
                    succeeded &= result_pg.succeeded
                result_logs = await rotate_logs(ib_name)
                succeeded &= result_logs.succeeded
                return core_models.InfoBaseMaintenanceTaskResult(ib_name, succeeded)
            else:
                return await _maintenance_v8(ib_name)
        except Exception:
            log.exception(f"<{ib_name}> Unknown exception occurred in coroutine")
            return core_models.InfoBaseMaintenanceTaskResult(ib_name, False)


def analyze_results(
    infobases: List[str],
    update_result: List[core_models.InfoBaseMaintenanceTaskResult],
    update_datetime_start: datetime,
    update_datetime_finish: datetime,
):
    analyze_maintenance_result(update_result, infobases, update_datetime_start, update_datetime_finish)


async def main():
    try:
        info_bases = utils.get_info_bases()
        maintenance_semaphore = initialize_semaphore(settings.MAINTENANCE_CONCURRENCY, log_prefix, "maintenance")

        maintenance_datetime_start = datetime.now()
        maintenance_results = await asyncio.gather(
            *[maintenance_info_base(ib_name, maintenance_semaphore) for ib_name in info_bases]
        )
        maintenance_datetime_finish = datetime.now()

        analyze_results(
            info_bases,
            maintenance_results,
            maintenance_datetime_start,
            maintenance_datetime_finish,
        )

        log.info(f"<{log_prefix}> Done")
    except Exception:
        log.exception(f"<{log_prefix}> Unknown exception occured in main coroutine")


if __name__ == "__main__":
    configure_logging(settings.LOG_LEVEL)
    initialize_event_loop(main())
