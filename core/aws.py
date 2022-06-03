import asyncio
import aioboto3
import os
import logging
import settings
from typing import List

from botocore.exceptions import EndpointConnectionError
from datetime import datetime, timedelta, timezone

import core.common as common_funcs
import core.types as core_types


retention_days = settings.AWS_RETENTION_DAYS


log = logging.getLogger(__name__)
log_prefix = 'AWS'


def sizeof_fmt(num, suffix='B', radix=1024.0):
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < radix:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= radix
    return "%.1f%s%s" % (num, 'Yi', suffix)


def analyze_s3_result(resultset: List[core_types.InfoBaseAWSUploadTaskResult], workload: List[str], datetime_start: datetime, datetime_finish: datetime):
    succeeded = 0
    failed = 0
    size = 0
    if len(resultset) > 0:
        for task_result in resultset:
            if task_result.succeeded:
                succeeded += 1
                size += task_result.upload_size
            else:
                failed += 1
                log.error(f'<{log_prefix}> [{task_result.infobase_name}] FAILED')
        diff = (datetime_finish - datetime_start).total_seconds()
        log.info(f'<{log_prefix}> {succeeded} succeeded; {failed} failed; Uploaded {sizeof_fmt(size)} in {diff:.1f}s. Avg. speed {sizeof_fmt(size / diff)}/s')
        if len(resultset) != len(workload):
            processed_info_bases = [task_result.infobase_name for task_result in resultset]
            missed = 0
            for w in workload:
                if w not in processed_info_bases:
                    log.warning(f'<{log_prefix}> [{w}] MISSED')
                    missed += 1
            log.warning(f'<{log_prefix}> {len(workload)} required; {len(resultset)} done; {missed} missed')
    else:
        log.info(f'<{log_prefix}> Nothing done')


async def upload_infobase_to_s3(ib_name: str, full_backup_path: str, semaphore: asyncio.Semaphore) -> core_types.InfoBaseAWSUploadTaskResult:
    aws_retries = settings.AWS_RETRIES
    async with semaphore:
        try:
            # Добавляем 1 к количеству повторных попыток, потому что одну попытку всегда нужно делать
            for i in range(0, aws_retries + 1):
                try:
                    return await _upload_infobase_to_s3(ib_name, full_backup_path)
                except EndpointConnectionError as e:
                    # Если количество попыток исчерпано, но ошибка по прежнему присутствует
                    if i == aws_retries:
                        raise e
                    else:
                        log.debug(f'<{ib_name}> AWS upload failed, retrying')
                        aws_retry_pause = settings.AWS_RETRY_PAUSE
                        log.debug(f'<{ib_name}> wait for {aws_retry_pause} seconds')
                        await asyncio.sleep(aws_retry_pause)
        except Exception as e:
            log.exception(f'<{ib_name}> Unknown exception occurred in AWS coroutine')
            return core_types.InfoBaseAWSUploadTaskResult(ib_name, False)


async def _upload_infobase_to_s3(ib_name: str, full_backup_path: str) -> core_types.InfoBaseAWSUploadTaskResult:
    log.info(f'<{ib_name}> Start upload {full_backup_path} to Amazon S3')
    session = aioboto3.Session(
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION_NAME
    )
    async with session.resource(service_name='s3', endpoint_url=settings.AWS_ENDPOINT_URL) as s3:
        bucket_name = settings.AWS_BUCKET_NAME
        filename = common_funcs.path_leaf(full_backup_path)
        # Собираем инфу чтобы вывод в лог был полезным
        filestat = os.stat(full_backup_path)
        source_size = filestat.st_size
        datetime_start = datetime.now()
        async with session.client(service_name='s3', endpoint_url=settings.AWS_ENDPOINT_URL) as s3c:
            await s3c.upload_file(Filename=full_backup_path, Bucket=bucket_name, Key=filename)
        datetime_finish = datetime.now()
        diff = (datetime_finish - datetime_start).total_seconds()
        log.info(f'<{ib_name}> Uploaded {sizeof_fmt(source_size)} in {diff:.1f}s. Avg. speed {sizeof_fmt(source_size / diff)}/s')
        # Имена файлов обязательно должны быть в формате ИмяИБ_ДатаСоздания
        # '_' добавляется к имени ИБ, чтобы по ошибке не получить файлы от другой ИБ
        # при наличии имён вида infobase и infobase2
        bucket = await s3.Bucket(bucket_name)
        async for o in bucket.objects.filter(Prefix=ib_name + '_'):
            if await o.last_modified < (datetime.now() - timedelta(days=retention_days)).replace(tzinfo=timezone.utc):
                await o.delete()
    return core_types.InfoBaseAWSUploadTaskResult(ib_name, True, source_size)


async def upload_to_s3(backup_results: core_types.InfoBaseBackupTaskResult):
    """
    Загружает резервные копии информационных баз в Amazon S3.
    Распаралеливает задачу т.к. одна загрузка ограничена скоростью ~8 Мбит/с
    """
    if settings.AWS_ENABLED:
        concurrency = settings.AWS_CONCURRENCY
        semaphore = asyncio.Semaphore(concurrency)
        log.info(f'<{log_prefix}> Asyncio semaphore initialized: {concurrency} concurrent tasks')
        datetime_start = datetime.now()
        result = await asyncio.gather([
            upload_infobase_to_s3(
                    backup_result.infobase_name, 
                    backup_result.backup_filename, 
                    semaphore
                ) for backup_result in backup_results
            ])
        datetime_finish = datetime.now()
        analyze_s3_result(result, datetime_start, datetime_finish)
