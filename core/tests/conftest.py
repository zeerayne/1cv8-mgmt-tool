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

    resource = MagicMock(AsyncContextManagerStub())
    client = MagicMock(AsyncContextManagerStub())

    # TODO: doesn't know how to properly mock async iterator so deep inside other mock
    mocker.patch('core.aws._remove_old_infobase_backups_from_s3', AsyncMock())

    aioboto3_session_mock = Mock()
    aioboto3_session_mock.resource = resource
    aioboto3_session_mock.client = client
    return mocker.patch('aioboto3.Session', return_value=aioboto3_session_mock)


@pytest.fixture
def mock_os_stat(mocker: MockerFixture):
    os_stat_mock = Mock()
    os_stat_mock.st_size = 1000
    return mocker.patch('os.stat', return_value=os_stat_mock)
