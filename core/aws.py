import boto3
import os
import logging
import math
import settings
import time
from botocore.exceptions import EndpointConnectionError
from datetime import datetime, timedelta, timezone
from multiprocessing.pool import ThreadPool

import core.common as common_funcs


session = boto3.Session(
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION_NAME
    )
s3 = session.resource(service_name='s3', endpoint_url=settings.AWS_ENDPOINT_URL)
s3c = session.client(service_name='s3', endpoint_url=settings.AWS_ENDPOINT_URL)
bucket = s3.Bucket(settings.AWS_BUCKET_NAME)
retention_days = settings.AWS_RETENTION_DAYS


log = logging.getLogger(__name__)
log_prefix = 'AWS'


def sizeof_fmt(num, suffix='B', radix=1024.0):
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < radix:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= radix
    return "%.1f%s%s" % (num, 'Yi', suffix)


def analyze_s3_result(result, workload, datetime_start, datetime_finish):
    succeeded = 0
    failed = 0
    size = 0
    if len(result) > 0:
        for e in result:
            if e[1]:
                succeeded += 1
                size += e[2]
            else:
                failed += 1
                log.error(f'<{log_prefix}> [{e[0]}] FAILED')
        diff = (datetime_finish - datetime_start).total_seconds()
        log.info(f'<{log_prefix}> {succeeded} succeeded; {failed} failed; Uploaded {sizeof_fmt(size)} in {diff:.1f}s. Avg. speed {sizeof_fmt(size / diff)}/s')
        if len(result) != len(workload):
            processed_info_bases = [e[0] for e in result]
            missed = 0
            for w in workload:
                if w not in processed_info_bases:
                    log.warning(f'<{log_prefix}> [{w}] MISSED')
                    missed += 1
            log.warning(f'<{log_prefix}> {len(workload)} required; {len(result)} done; {missed} missed')
    else:
        log.info(f'<{log_prefix}> Nothing done')


def upload_infobase_to_s3(ib_name, full_backup_path):
    aws_retries = settings.AWS_RETRIES
    try:
        # Добавляем 1 к количеству повторных попыток, потому что одну попытку всегда нужно делать
        for i in range(0, aws_retries + 1):
            try:
                result = _upload_infobase_to_s3(ib_name, full_backup_path)
                return result
            except EndpointConnectionError as e:
                # Если количество попыток исчерпано, но ошибка по прежнему присутствует
                if i == aws_retries:
                    raise e
                else:
                    log.debug(f'<{ib_name}> AWS upload failed, retrying')
                    aws_retry_pause = settings.AWS_RETRY_PAUSE
                    log.debug(f'<{ib_name}> wait for {aws_retry_pause} seconds')
                    time.sleep(aws_retry_pause)
    except Exception as e:
        log.exception(f'<{ib_name}> Unknown exception occurred in AWS thread')
        return ib_name, False


def _upload_infobase_to_s3(ib_name, full_backup_path):
    log.info(f'<{ib_name}> Start upload {full_backup_path} to Amazon S3')
    bucket_name = settings.AWS_BUCKET_NAME
    bucket_obj = bucket
    file_mime = 'application/octet-stream'
    filename = common_funcs.path_leaf(full_backup_path)
    # Собираем инфу чтобы вывод в лог был полезным
    filestat = os.stat(full_backup_path)
    source_size = filestat.st_size
    datetime_start = datetime.now()
    chunk_size = settings.AWS_CHUNK_SIZE
    if source_size > chunk_size:
        chunk_count = math.ceil(source_size / chunk_size)
        log.info(
            f'<{ib_name}> File size is {sizeof_fmt(source_size)}, chunk size is {sizeof_fmt(chunk_size)}. '
            f'Multipart upload for {chunk_count} chunks'
        )
    tc = boto3.s3.transfer.TransferConfig(
        multipart_threshold=chunk_size, 
        multipart_chunksize=chunk_size 
    )
    s3c.upload_file(Filename=full_backup_path, Bucket=bucket_name, Key=filename, Config=tc)
    datetime_finish = datetime.now()
    diff = (datetime_finish - datetime_start).total_seconds()
    log.info(f'<{ib_name}> Uploaded {sizeof_fmt(source_size)} in {diff:.1f}s. Avg. speed {sizeof_fmt(source_size / diff)}/s')
    # Имена файлов обязательно должны быть в формате ИмяИБ_ДатаСоздания
    # '_' добавляется к имени ИБ, чтобы по ошибке не получить файлы от другой ИБ
    # при наличии имён вида infobase и infobase2
    objs = bucket_obj.objects.filter(Prefix=ib_name + '_')
    for o in objs:
        if o.last_modified < (datetime.now() - timedelta(days=retention_days)).replace(tzinfo=timezone.utc):
            o.delete()
    return ib_name, True, source_size


def upload_to_s3(infobases):
    """
    Загружает резервные копии информационных баз в Amazon S3.
    Распаралеливает задачу т.к. одна загрузка ограничена скоростью ~8 Мбит/с
    :param infobases: Структура вида [(ib_name_1, path_to_backup_file_1), (ib_name_2, path_to_backup_file_2), ]
    :return:
    """
    if settings.AWS_ENABLED:
        threads = settings.AWS_THREADS
        log.debug(f'<{log_prefix}> Creating pool with {threads} threads')
        pool = ThreadPool(threads)
        log.debug(f'<{log_prefix}> Pool initialized, mapping workload: {len(infobases)} items')
        datetime_start = datetime.now()
        result = pool.starmap(upload_infobase_to_s3, infobases)
        datetime_finish = datetime.now()
        log.debug(f'<{log_prefix}> Closing pool')
        pool.close()
        log.debug(f'<{log_prefix}> Joining pool')
        pool.join()
        analyze_s3_result(result, datetime_start, datetime_finish)
