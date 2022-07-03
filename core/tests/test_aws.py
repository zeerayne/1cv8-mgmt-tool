import asyncio
from functools import reduce
from unittest.mock import AsyncMock, PropertyMock

import pytest
from pytest_mock import MockerFixture

from conf import settings
from core.aws import (
    _get_aws_endpoint_url_parameter, _get_aws_region_parameter, _remove_old_infobase_backups_from_s3,
    _upload_infobase_to_s3, upload_infobase_to_s3, upload_to_s3
)


def test_get_aws_endpoint_url_parameter_returns_dict_if_not_set():
    """
    Default AWS endpoint url parameter is dict
    """
    result = _get_aws_endpoint_url_parameter()
    assert isinstance(result, dict)


def test_get_aws_endpoint_url_parameter_returns_dict_if_set(mocker: MockerFixture):
    """
    Custom AWS endpoint url parameter is dict
    """
    mocker.patch('conf.settings.AWS_ENDPOINT_URL', new_callable=PropertyMock(return_value='test.aws.endpoint'))
    result = _get_aws_endpoint_url_parameter()
    assert isinstance(result, dict)


def test_get_aws_endpoint_url_parameter_returns_empty_dict_if_not_set():
    """
    Default AWS endpoint url parameter is empty
    """
    result = _get_aws_endpoint_url_parameter()
    assert not result


def test_get_aws_endpoint_url_parameter_returns_dict_with_value_if_set(mocker: MockerFixture):
    """
    Custom AWS endpoint url parameter contatins parameter name and value
    """
    endpoint_url = 'test.aws.endpoint'
    mocker.patch('conf.settings.AWS_ENDPOINT_URL', new_callable=PropertyMock(return_value=endpoint_url))
    result = _get_aws_endpoint_url_parameter()
    assert result['endpoint_url'] == endpoint_url


def test_get_aws_region_parameter_returns_dict_if_not_set():
    """
    Default AWS region name parameter is dict
    """
    result = _get_aws_region_parameter()
    assert isinstance(result, dict)


def test_get_aws_region_parameter_returns_dict_if_set(mocker: MockerFixture):
    """
    Custom AWS region name parameter is dict
    """
    mocker.patch('conf.settings.AWS_REGION_NAME', new_callable=PropertyMock(return_value='test-us-east-1'))
    result = _get_aws_region_parameter()
    assert isinstance(result, dict)


def test_get_aws_region_parameter_returns_empty_dict_if_not_set():
    """
    Default AWS region name parameter is empty
    """
    result = _get_aws_region_parameter()
    assert not result


def test_get_aws_region_parameter_returns_dict_with_value_if_set(mocker: MockerFixture):
    """
    Custom AWS region name parameter contatins parameter name and value
    """
    region_name = 'test-us-east-1'
    mocker.patch('conf.settings.AWS_REGION_NAME', new_callable=PropertyMock(return_value=region_name))
    result = _get_aws_region_parameter()
    assert result['region_name'] == region_name


@pytest.mark.asyncio()
async def test_upload_infobase_to_s3_return_success_result_for_exact_infobase(
    infobase, success_backup_result, mock_upload_infobase_to_s3
):
    """
    AWS uploader should return InfoBaseAWSUploadTaskResult for exact infobase which was provided if no errors
    """
    aws_semaphore = asyncio.Semaphore(1)
    result = await upload_infobase_to_s3(infobase, success_backup_result[0].backup_filename, aws_semaphore)
    assert result.infobase_name == infobase


@pytest.mark.asyncio()
async def test_upload_infobase_to_s3_return_success_result(infobase, success_backup_result, mock_upload_infobase_to_s3):
    """
    AWS uploader should return InfoBaseAWSUploadTaskResult with `success=True` if no errors
    """
    aws_semaphore = asyncio.Semaphore(1)
    result = await upload_infobase_to_s3(infobase, success_backup_result[0].backup_filename, aws_semaphore)
    assert result.succeeded is True


@pytest.mark.asyncio()
async def test_upload_infobase_to_s3_return_failed_result_for_exact_infobase(
    infobase, success_backup_result, mock_upload_infobase_to_s3_connection_error
):
    """
    AWS uploader should return InfoBaseAWSUploadTaskResult for exact infobase which was provided if can't upload
    """
    aws_semaphore = asyncio.Semaphore(1)
    result = await upload_infobase_to_s3(infobase, success_backup_result[0].backup_filename, aws_semaphore)
    assert result.infobase_name == infobase


@pytest.mark.asyncio()
async def test_upload_infobase_to_s3_return_failed_result(
    infobase, success_backup_result, mock_upload_infobase_to_s3_connection_error
):
    """
    AWS uploader should return InfoBaseAWSUploadTaskResult with `success=False` if can't upload
    """
    aws_semaphore = asyncio.Semaphore(1)
    result = await upload_infobase_to_s3(infobase, success_backup_result[0].backup_filename, aws_semaphore)
    assert result.succeeded is False


@pytest.mark.asyncio()
async def test_upload_infobase_to_s3_make_retries(
    infobase, success_backup_result, mock_upload_infobase_to_s3_connection_error
):
    """
    AWS uploader should retry if there is connection issues during upload
    """
    aws_semaphore = asyncio.Semaphore(1)
    await upload_infobase_to_s3(infobase, success_backup_result[0].backup_filename, aws_semaphore)
    # + 1 is for non-retry call
    assert mock_upload_infobase_to_s3_connection_error.call_count == settings.AWS_RETRIES + 1


@pytest.mark.asyncio()
async def test_internal_upload_infobase_to_s3_call(
    mocker: MockerFixture, infobase, success_backup_result, mock_aioboto3_session, mock_os_stat
):
    """
    boto3.Session.client.upload_file inside should be called when uploading files to AWS
    """
    mocker.patch('core.aws._remove_old_infobase_backups_from_s3', AsyncMock())
    await _upload_infobase_to_s3(infobase, success_backup_result[0].backup_filename)
    mock_aioboto3_session.return_value.client.return_value.__aenter__.return_value.upload_file.assert_awaited_once()


@pytest.mark.asyncio()
async def test_old_infobase_backups_from_s3_are_removed(mock_aioboto3_session, mock_aioboto3_bucket_objects_old):
    """
    Backups older than `settings.AWS_RETENTION_DAYS` are removed from S3
    """
    await _remove_old_infobase_backups_from_s3('', mock_aioboto3_session)
    mock_aioboto3_bucket_objects_old.delete.assert_awaited()


@pytest.mark.asyncio()
async def test_new_infobase_backups_from_s3_are_not_removed(mock_aioboto3_session, mock_aioboto3_bucket_objects_new):
    """
    Backups newer than `settings.AWS_RETENTION_DAYS` are not removed from S3
    """
    await _remove_old_infobase_backups_from_s3('', mock_aioboto3_session)
    mock_aioboto3_bucket_objects_new.delete.assert_not_awaited()


@pytest.mark.asyncio()
async def test_upload_to_s3(mocker: MockerFixture, mock_upload_infobase_to_s3, mixed_backup_result):
    """
    When uploading infobases backups to s3 `upload_infobase_to_s3` should be called for every successful backup result
    """
    mocker.patch('core.analyze._analyze_result')
    mocker.patch('conf.settings.AWS_ENABLED', new_callable=PropertyMock(return_value=True))
    await upload_to_s3(mixed_backup_result)
    assert mock_upload_infobase_to_s3.await_count == reduce(
        lambda prev, curr: prev + int(curr.succeeded), mixed_backup_result, 0
    )
