import random
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, Mock, PropertyMock

import pytest
from botocore.exceptions import EndpointConnectionError
from pytest_mock import MockerFixture

from conf import settings
from core import models as core_models

random.seed(0)


@pytest.fixture()
def mock_analyze_result(mocker: MockerFixture):
    return mocker.patch("core.analyze.analyze_result", return_value=None)


@pytest.fixture()
async def mock_upload_infobase_to_s3(mocker: MockerFixture):
    async_mock = AsyncMock(
        side_effect=lambda ib_name, full_backup_path: core_models.InfoBaseAWSUploadTaskResult(ib_name, True, 1000)
    )
    return mocker.patch("core.aws._upload_infobase_to_s3", side_effect=async_mock)


@pytest.fixture()
async def mock_upload_infobase_to_s3_connection_error(mocker: MockerFixture):
    async_mock = AsyncMock(side_effect=EndpointConnectionError(endpoint_url="http://test.endpoint.url"))
    return mocker.patch("core.aws._upload_infobase_to_s3", side_effect=async_mock)


@pytest.fixture()
async def mock_aioboto3_session(mocker: MockerFixture):
    aioboto3_session_mock = Mock()

    resource = MagicMock()
    type(aioboto3_session_mock).resource = resource

    client = MagicMock()
    type(aioboto3_session_mock).client = client

    return mocker.patch("aioboto3.Session", return_value=aioboto3_session_mock)


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


@pytest.fixture()
async def mock_aioboto3_bucket_objects_old(mock_aioboto3_session):
    from conf import settings

    return create_bucket_object(
        mock_aioboto3_session, datetime.now(tz=timezone.utc) - timedelta(days=settings.AWS_RETENTION_DAYS + 2)
    )


@pytest.fixture()
async def mock_aioboto3_bucket_objects_new(mock_aioboto3_session):
    return create_bucket_object(mock_aioboto3_session, datetime.now(tz=timezone.utc))


@pytest.fixture()
def mock_os_stat(mocker: MockerFixture):
    os_stat_mock = Mock()
    os_stat_mock.st_size = 1000
    return mocker.patch("os.stat", return_value=os_stat_mock)


@pytest.fixture()
def mock_os_platform_path(mocker: MockerFixture, mock_platform_versions):
    mocker.patch("os.path.isdir", return_value=True)
    return mocker.patch(
        "os.listdir", return_value=mock_platform_versions + ["test_common", "test_conf", "test_srvinfo"]
    )


@pytest.fixture()
def mock_platform_version():
    return f"8.3.{random.randint(15,25)}.{random.randint(1000,3000)}"


@pytest.fixture()
def mock_platform_last_version():
    return f"8.3.99.{random.randint(1000,3000)}"


@pytest.fixture()
def mock_platform_versions(mock_platform_version, mock_platform_last_version):
    return [mock_platform_version, mock_platform_last_version]


@pytest.fixture()
def mock_datetime():
    return datetime(2022, 1, 1, 12, 1, 1)


@pytest.fixture()
def mock_infobases_credentials(mocker: MockerFixture, infobases):
    creds = {infobase: (f"test_{infobase}_login", f"test_{infobase}_password") for infobase in infobases}
    creds.update(settings.V8_INFOBASES_CREDENTIALS)
    mocker.patch("conf.settings.V8_INFOBASES_CREDENTIALS", new_callable=PropertyMock(return_value=creds))
    return creds
