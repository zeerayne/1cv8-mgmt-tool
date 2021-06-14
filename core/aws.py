import boto3
import os
import math
import settings
import time
from botocore.exceptions import EndpointConnectionError
from datetime import datetime, timedelta, timezone
from multiprocessing.pool import ThreadPool

import core.common as common_funcs
import core.logging as logging


session = boto3.Session(
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION_NAME
    )
s3 = session.resource('s3')
s3c = session.client('s3')
bucket = s3.Bucket(settings.AWS_BUCKET_NAME)
retention_days = settings.AWS_RETENTION_DAYS


log = logging.getLogger(__name__)


def sizeof_fmt(num, suffix='B'):
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


@logging.logaugment_operation(log, 'aws')
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
                log.error('[{0}] FAILED'.format(e[0]))
        diff = (datetime_finish - datetime_start).total_seconds()
        log.info('{0} succeeded; {1} failed; Uploaded {2} in {3:.1f}s. Avg. speed {4}/s'
                 .format(succeeded, failed, sizeof_fmt(size), diff, sizeof_fmt(size / diff)))
        if len(result) != len(workload):
            processed_info_bases = [e[0] for e in result]
            missed = 0
            for w in workload:
                if w not in processed_info_bases:
                    log.warning('[%s] MISSED' % w)
                    missed += 1
            log.warning('{0} required; {1} done; {2} missed'
                        .format(len(workload), len(result), missed))
    else:
        log.info('Nothing done')


@logging.logaugment_ib_name_parameter_operation(log)
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
                    log.debug('AWS upload failed, retrying')
                    aws_retry_pause = settings.AWS_RETRY_PAUSE
                    log.debug(f'wait for {aws_retry_pause} seconds')
                    time.sleep(aws_retry_pause)
    except Exception as e:
        log.exception('Unknown exception occurred in AWS thread')
        return ib_name, False


@logging.logaugment_ib_name_parameter_operation(log)
def _upload_infobase_to_s3(ib_name, full_backup_path):
    log.info(f'Start upload {full_backup_path} to Amazon S3')
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
            f'File size is {sizeof_fmt(source_size)}, chunk size is {sizeof_fmt(chunk_size)}. '
            f'Multipart upload for {chunk_count} chunks'
        )
    tc = boto3.s3.transfer.TransferConfig(
        multipart_threshold=chunk_size, 
        multipart_chunksize=chunk_size 
    )
    s3c.upload_file(Filename=full_backup_path, Bucket=bucket_name, Key=filename, Config=tc)
    datetime_finish = datetime.now()
    diff = (datetime_finish - datetime_start).total_seconds()
    log.info(f'Uploaded {sizeof_fmt(source_size)} in {diff:.1f}s. Avg. speed {sizeof_fmt(source_size / diff)}/s')
    # Имена файлов обязательно должны быть в формате ИмяИБ_ДатаСоздания
    # '_' добавляется к имени ИБ, чтобы по ошибке не получить файлы от другой ИБ
    # при наличии имён вида infobase и infobase2
    objs = bucket_obj.objects.filter(Prefix=ib_name + '_')
    for o in objs:
        if o.last_modified < (datetime.now() - timedelta(days=retention_days)).replace(tzinfo=timezone.utc):
            o.delete()
    return ib_name, True, source_size


@logging.logaugment_operation(log, 'aws')
def upload_to_s3(infobases):
    """
    Загружает резервные копии информационных баз в Amazon S3.
    Распаралеливает задачу т.к. одна загрузка ограничена скоростью ~8 Мбит/с
    :param infobases: Структура вида [(ib_name_1, path_to_backup_file_1), (ib_name_2, path_to_backup_file_2), ]
    :return:
    """
    if settings.AWS_ENABLED:
        threads = settings.AWS_THREADS
        log.debug(f'Creating pool with {threads} threads')
        pool = ThreadPool(threads)
        log.debug(f'Pool initialized, mapping workload: {len(infobases)} items')
        datetime_start = datetime.now()
        result = pool.starmap(upload_infobase_to_s3, infobases)
        datetime_finish = datetime.now()
        log.debug('Closing pool')
        pool.close()
        log.debug('Joining pool')
        pool.join()
        analyze_s3_result(result, datetime_start, datetime_finish)
