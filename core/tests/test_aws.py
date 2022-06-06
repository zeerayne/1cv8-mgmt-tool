import asyncio

import pytest

from conf import settings
from core.aws import upload_infobase_to_s3, _upload_infobase_to_s3
from core import types as core_types


@pytest.mark.asyncio
async def test_upload_infobase_to_s3_return_success_result(infobases, success_backup_result, mock_upload_infobase_to_s3):
    """
    AWS uploader should return InfoBaseAWSUploadTaskResult with `success=True` if no errors
    """
    aws_semaphore = asyncio.Semaphore(1)
    result = await upload_infobase_to_s3(infobases[0], success_backup_result[0].backup_filename, aws_semaphore)
    compare = core_types.InfoBaseAWSUploadTaskResult(infobases[0], True)
    assert result.infobase_name == compare.infobase_name and result.succeeded == compare.succeeded


@pytest.mark.asyncio
async def test_upload_infobase_to_s3_return_failed_result(infobases, success_backup_result, mock_upload_infobase_to_s3_connection_error):
    """
    AWS uploader should return InfoBaseAWSUploadTaskResult with `success=False` if can't upload
    """
    aws_semaphore = asyncio.Semaphore(1)
    result = await upload_infobase_to_s3(infobases[0], success_backup_result[0].backup_filename, aws_semaphore)
    compare = core_types.InfoBaseAWSUploadTaskResult(infobases[0], False)
    assert result.infobase_name == compare.infobase_name and result.succeeded == compare.succeeded


@pytest.mark.asyncio
async def test_upload_infobase_to_s3_make_retries(infobases, success_backup_result, mock_upload_infobase_to_s3_connection_error):
    """
    AWS uploader should retry if there is connection issues during upload
    """
    aws_semaphore = asyncio.Semaphore(1)
    await upload_infobase_to_s3(infobases[0], success_backup_result[0].backup_filename, aws_semaphore)
    assert mock_upload_infobase_to_s3_connection_error.call_count == settings.AWS_RETRIES + 1  # + 1 is for non-retry call


@pytest.mark.asyncio
async def test_internal_upload_infobase_to_s3_call(infobases, success_backup_result, mock_aioboto3_session, mock_os_stat):
    """
    boto3.Session.client.upload_file inside should be called when uploading files to AWS
    """
    aws_semaphore = asyncio.Semaphore(1)
    await _upload_infobase_to_s3(infobases[0], success_backup_result[0].backup_filename)
    mock_aioboto3_session.return_value.client.return_value.__aenter__.return_value.upload_file.assert_called_once()
