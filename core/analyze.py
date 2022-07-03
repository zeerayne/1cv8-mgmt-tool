import functools
import logging
from datetime import datetime
from typing import Callable, List

import core.types as core_types
from utils.common import sizeof_fmt


log = logging.getLogger(__name__)
log_prefix = 'Analyze'


def _wrap_log_subprefix(log_subprefix):
    if log_subprefix:
        return f' | {log_subprefix}'
    else:
        return ''


def _log_message(
    resultset: List[core_types.InfoBaseTaskResultBase], succeeded: int, failed: int, datetime_start: datetime,
    datetime_finish: datetime, log_subprefix: str
):
    log_subprefix = _wrap_log_subprefix(log_subprefix)
    diff = (datetime_finish - datetime_start).total_seconds()
    log.info(
        f'<{log_prefix}{log_subprefix}> {succeeded} succeeded; {failed} failed; Avg. time {diff / len(resultset):.1f}s.'
    )


def _analyze_result(
    resultset: List[core_types.InfoBaseTaskResultBase],
    workload: List[str],
    datetime_start: datetime,
    datetime_finish: datetime,
    custom_log_message_func: Callable[[List[core_types.InfoBaseTaskResultBase], int, int, datetime, datetime],
                                      None] = None,
    log_subprefix: str = None
):
    log_subprefix = _wrap_log_subprefix(log_subprefix)
    succeeded = 0
    failed = 0
    if resultset:
        for task_result in resultset:
            if task_result.succeeded:
                succeeded += 1
            else:
                failed += 1
                log.error(f'<{log_prefix}{log_subprefix}> [{task_result.infobase_name}] FAILED')
        if custom_log_message_func:
            custom_log_message_func(resultset, succeeded, failed, datetime_start, datetime_finish)
    if len(resultset) != len(workload):
        processed_info_bases = [task_result.infobase_name for task_result in resultset]
        missed = 0
        for w in workload:
            if w not in processed_info_bases:
                log.warning(f'<{log_prefix}{log_subprefix}> [{w}] MISSED')
                missed += 1
        log.warning(f'<{log_prefix}{log_subprefix}> {len(workload)} required; {len(resultset)} done; {missed} missed')
    if not (resultset and workload):
        log.info(f'<{log_prefix}{log_subprefix}> Nothing was done')


def analyze_result(
    resultset: List[core_types.InfoBaseTaskResultBase],
    workload: List[str],
    datetime_start: datetime,
    datetime_finish: datetime,
    log_subprefix: str = None
):
    log_message = functools.partial(_log_message, log_subprefix=log_subprefix)
    _analyze_result(resultset, workload, datetime_start, datetime_finish, log_message, log_subprefix)


def analyze_s3_result(
    resultset: List[core_types.InfoBaseAWSUploadTaskResult], workload: List[str], datetime_start: datetime,
    datetime_finish: datetime
):
    log_subprefix = _wrap_log_subprefix('AWS')

    def log_message(
        resultset: List[core_types.InfoBaseTaskResultBase], succeeded: int, failed: int, datetime_start: datetime,
        datetime_finish: datetime
    ):
        size = 0
        for task_result in resultset:
            if task_result.succeeded:
                size += task_result.upload_size
        diff = (datetime_finish - datetime_start).total_seconds()
        log.info(
            f'<{log_prefix}{log_subprefix}> {succeeded} succeeded; {failed} failed; Uploaded {sizeof_fmt(size)} in {diff:.1f}s. Avg. speed {sizeof_fmt(size / diff)}/s'
        )

    _analyze_result(resultset, workload, datetime_start, datetime_finish, log_message, log_subprefix)


def analyze_backup_result(
    resultset: List[core_types.InfoBaseBackupTaskResult], workload: List[str], datetime_start: datetime,
    datetime_finish: datetime
):
    log_subprefix = 'Backup'
    analyze_result(resultset, workload, datetime_start, datetime_finish, log_subprefix)


def analyze_maintenance_result(
    resultset: List[core_types.InfoBaseBackupTaskResult], workload: List[str], datetime_start: datetime,
    datetime_finish: datetime
):
    log_subprefix = 'Maintenance'
    analyze_result(resultset, workload, datetime_start, datetime_finish, log_subprefix)


def analyze_update_result(
    resultset: List[core_types.InfoBaseBackupTaskResult], workload: List[str], datetime_start: datetime,
    datetime_finish: datetime
):
    log_subprefix = 'Update'
    analyze_result(resultset, workload, datetime_start, datetime_finish, log_subprefix)
