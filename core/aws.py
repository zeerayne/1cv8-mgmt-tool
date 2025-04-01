import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Dict

import aioboto3
import boto3
from botocore.exceptions import EndpointConnectionError

import core.models as core_models
from conf import settings
from core import utils
from core.analyze import analyze_s3_result
from utils.common import sizeof_fmt

log = logging.getLogger(__name__)
log_prefix = "AWS"


def _get_aws_endpoint_url_parameter() -> Dict[str, str]:
    url = settings.AWS_ENDPOINT_URL
    if url:
        return dict(endpoint_url=url)
    else:
        return dict()


def _get_aws_region_parameter() -> Dict[str, str]:
    region = settings.AWS_REGION_NAME
    if region:
        return dict(region_name=region)
    else:
        return dict()


async def upload_infobase_to_s3(
    ib_name: str, full_backup_path: str, semaphore: asyncio.Semaphore
) -> core_models.InfoBaseAWSUploadTaskResult:
    aws_retries = settings.AWS_RETRIES
    aws_upload_timeout = settings.AWS_UPLOAD_TIMEOUT
    async with semaphore:
        try:
            # Добавляет 1 к количеству повторных попыток, потому что одну попытку всегда нужно делать
            for i in range(0, aws_retries + 1):
                try:
                    # Changed in version 3.11: Raises TimeoutError instead of asyncio.TimeoutError
                    return await asyncio.wait_for(
                        _upload_infobase_to_s3(ib_name, full_backup_path), timeout=aws_upload_timeout
                    )
                except (EndpointConnectionError, asyncio.TimeoutError, TimeoutError) as e:
                    # Если количество попыток исчерпано, но ошибка по прежнему присутствует
                    if i == aws_retries:
                        raise e
                    else:
                        log.debug(f"<{ib_name}> AWS upload failed, retrying")
                        aws_retry_pause = settings.AWS_RETRY_PAUSE
                        log.debug(f"<{ib_name}> wait for {aws_retry_pause} seconds")
                        await asyncio.sleep(aws_retry_pause)
        except Exception:
            log.exception(f"<{ib_name}> Unknown exception occurred in AWS coroutine")
            return core_models.InfoBaseAWSUploadTaskResult(ib_name, False)


async def _upload_infobase_to_s3(ib_name: str, full_backup_path: str) -> core_models.InfoBaseAWSUploadTaskResult:
    log.info(f"<{ib_name}> Start upload {full_backup_path} to Amazon S3")
    session = aioboto3.Session(
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        **_get_aws_region_parameter(),
    )
    filename = utils.path_leaf(full_backup_path)
    # Собирает инфу чтобы вывод в лог был полезным
    filestat = os.stat(full_backup_path)
    source_size = filestat.st_size
    datetime_start = datetime.now()
    async with session.client(service_name="s3", **_get_aws_endpoint_url_parameter()) as s3c:
        await s3c.upload_file(Filename=full_backup_path, Bucket=settings.AWS_BUCKET_NAME, Key=filename)
    datetime_finish = datetime.now()
    diff = (datetime_finish - datetime_start).total_seconds() or 1
    log.info(
        f"<{ib_name}> Uploaded {sizeof_fmt(source_size)} in {diff:.1f}s. Avg. speed {sizeof_fmt(source_size / diff)}/s"
    )
    await _remove_old_infobase_backups_from_s3(ib_name, session)
    return core_models.InfoBaseAWSUploadTaskResult(ib_name, True, source_size)


async def _remove_old_infobase_backups_from_s3(ib_name: str, session: boto3.Session):
    # Имена файлов обязательно должны быть в формате ИмяИБ_ДатаСоздания
    # `get_ib_name_with_separator` используется вместо имени ИБ, чтобы по ошибке не получить файлы от другой ИБ
    # при наличии имён вида infobase и infobase2
    async with session.resource(service_name="s3", **_get_aws_endpoint_url_parameter()) as s3_resource:
        bucket = await s3_resource.Bucket(settings.AWS_BUCKET_NAME)
        async for o in bucket.objects.filter(Prefix=f"{utils.get_ib_name_with_separator(ib_name)}"):
            if await o.last_modified < (datetime.now() - timedelta(days=settings.AWS_RETENTION_DAYS)).replace(
                tzinfo=timezone.utc
            ):
                await o.delete()


async def upload_to_s3(backup_results: core_models.InfoBaseBackupTaskResult):
    """
    Загружает резервные копии информационных баз в Amazon S3.
    Распаралеливает задачу т.к. одна загрузка ограничена скоростью ~8 Мбит/с
    """
    if settings.AWS_ENABLED:
        concurrency = settings.AWS_CONCURRENCY
        semaphore = asyncio.Semaphore(concurrency)
        log.info(f"<{log_prefix}> Asyncio semaphore initialized: {concurrency} concurrent tasks")
        datetime_start = datetime.now()
        result = await asyncio.gather(
            *[
                upload_infobase_to_s3(
                    backup_result.infobase_name,
                    backup_result.backup_filename,
                    semaphore,
                )
                for backup_result in backup_results
                if backup_result.succeeded
            ]
        )
        datetime_finish = datetime.now()
        analyze_s3_result(
            result,
            [e.infobase_name for e in backup_results],
            datetime_start,
            datetime_finish,
        )
