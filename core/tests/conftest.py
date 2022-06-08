from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from botocore.exceptions import EndpointConnectionError
from pytest_mock import MockerFixture

from core import types as core_types


@pytest.fixture
def mock_analyze_result(mocker: MockerFixture):
    return mocker.patch('core.analyze.analyze_result', return_value=None)


@pytest.fixture
async def mock_upload_infobase_to_s3(mocker: MockerFixture):
    async_mock = AsyncMock(side_effect=lambda ib_name, full_backup_path: core_types.InfoBaseAWSUploadTaskResult(ib_name, True, 1000))
    return mocker.patch('core.aws._upload_infobase_to_s3', side_effect=async_mock)


@pytest.fixture
async def mock_upload_infobase_to_s3_connection_error(mocker: MockerFixture):
    async_mock = AsyncMock(side_effect=EndpointConnectionError(endpoint_url='http://test.endpoint.url'))
    return mocker.patch('core.aws._upload_infobase_to_s3', side_effect=async_mock)


@pytest.fixture
async def mock_aioboto3_session(mocker: MockerFixture):
    class AsyncContextManagerStub:

        async def __aenter__(self, *args, **kwargs):
            return self

        async def __aexit__(self, *args, **kwargs):
            pass

    aioboto3_session_mock = Mock()

    resource = MagicMock(AsyncContextManagerStub())
    aioboto3_session_mock.resource = resource

    client = MagicMock(AsyncContextManagerStub())
    aioboto3_session_mock.client = client

    return mocker.patch('aioboto3.Session', return_value=aioboto3_session_mock)


def create_bucket_object(mock_aioboto3_session, last_modified: datetime):

    class AsyncIteratorStub:
        def __init__(self, seq):
            self.iter = iter(seq)

        def __aiter__(self):
            return self

        async def __anext__(self):
            try:
                return next(self.iter)
            except StopIteration:
                raise StopAsyncIteration

    bucket_obj = AsyncMock()
    bucket_obj.last_modified = AsyncMock(return_value=last_modified)()

    resource = mock_aioboto3_session.resource

    bucket = AsyncMock()
    type(resource.return_value.__aenter__.return_value).Bucket = bucket

    bucket_objects = Mock()
    type(bucket.return_value).objects = bucket_objects

    bucket_objects_filter = MagicMock(return_value=AsyncIteratorStub([bucket_obj]))
    type(bucket_objects).filter = bucket_objects_filter

    return bucket_obj


@pytest.fixture
async def mock_aioboto3_bucket_objects_old(mock_aioboto3_session):
    from conf import settings
    return create_bucket_object(mock_aioboto3_session, datetime.now(tz=timezone.utc) - timedelta(days=settings.AWS_RETENTION_DAYS + 2))


@pytest.fixture
async def mock_aioboto3_bucket_objects_new(mock_aioboto3_session):
    return create_bucket_object(mock_aioboto3_session, datetime.now(tz=timezone.utc))


@pytest.fixture
def mock_os_stat(mocker: MockerFixture):
    os_stat_mock = Mock()
    os_stat_mock.st_size = 1000
    return mocker.patch('os.stat', return_value=os_stat_mock)
