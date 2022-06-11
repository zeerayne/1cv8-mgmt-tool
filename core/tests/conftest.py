import random
import re

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from botocore.exceptions import EndpointConnectionError
from pytest_mock import MockerFixture

from core import types as core_types
from core.surrogate import surrogate


random.seed(0)


@pytest.fixture
def mock_analyze_result(mocker: MockerFixture):
    return mocker.patch('core.analyze.analyze_result', return_value=None)


@pytest.fixture
async def mock_upload_infobase_to_s3(mocker: MockerFixture):
    async_mock = AsyncMock(
        side_effect=lambda ib_name, full_backup_path: core_types.InfoBaseAWSUploadTaskResult(ib_name, True, 1000)
    )
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
    type(aioboto3_session_mock).resource = resource

    client = MagicMock(AsyncContextManagerStub())
    type(aioboto3_session_mock).client = client

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


@pytest.fixture
def mock_infobase_version():
    return f'{random.randint(1,12)}.{random.randint(0,5)}.{random.randint(10,200)}'


@pytest.fixture
def mock_platform_version():
    return f'8.3.{random.randint(15,25)}.{random.randint(1000,3000)}'


@pytest.fixture
def mock_platform_last_version():
    return f'8.3.99.{random.randint(1000,3000)}'


@pytest.fixture
def mock_platform_versions(mock_platform_version, mock_platform_last_version):
    return [mock_platform_version, mock_platform_last_version]


@surrogate('win32com.client')
@pytest.fixture
def mock_win32com_client_dispatch(mocker: MockerFixture):
    import win32com.client as win32com_client
    return mocker.patch.object(win32com_client, 'Dispatch', create=True, return_value=Mock())


@pytest.fixture
def mock_infobases_com_obj(infobases):
    infobases_com_obj = []
    for ib in infobases:
        infobase_com_obj_mock = Mock()
        type(infobase_com_obj_mock).Name = ib
        infobases_com_obj.append(infobase_com_obj_mock)
    return Mock(return_value=infobases_com_obj)


@pytest.fixture
def mock_connect_agent(mock_win32com_client_dispatch, mock_infobases_com_obj):
    agent_connection_mock = Mock()
    
    type(agent_connection_mock.return_value).GetInfoBases = mock_infobases_com_obj
    type(agent_connection_mock.return_value).Authenticate = Mock()
    type(agent_connection_mock.return_value).GetClusters = Mock(return_value=['test_cluster01', 'test_cluster02'])
    
    working_process_mock = Mock()
    type(working_process_mock).MainPort = random.randint(1000, 2000)
    type(agent_connection_mock.return_value).GetWorkingProcesses = Mock(return_value=[working_process_mock])

    type(agent_connection_mock.return_value).GetInfoBaseSessions = Mock(
        side_effect=lambda cluster, info_base_short: [f'test_{info_base_short.Name}_session_{i}' for i in range(1,5)]
    )

    type(mock_win32com_client_dispatch.return_value).ConnectAgent = agent_connection_mock
    return agent_connection_mock


@pytest.fixture
def mock_connect_working_process(mock_win32com_client_dispatch, mock_infobases_com_obj):
    working_process_connection_mock = Mock()
    type(working_process_connection_mock.return_value).AuthenticateAdmin = Mock()
    type(working_process_connection_mock.return_value).AddAuthentication = Mock()
    type(working_process_connection_mock.return_value).GetInfoBases = mock_infobases_com_obj
    type(working_process_connection_mock.return_value).UpdateInfoBase = Mock()

    type(mock_win32com_client_dispatch.return_value).ConnectWorkingProcess = working_process_connection_mock
    return working_process_connection_mock


@pytest.fixture
def mock_external_connection(mock_win32com_client_dispatch, mock_infobase_version):
    def external_connection_mock_side_effect(connection_string):
        infobase_name = re.search(r'Ref="(?P<ref>[\w\d\-_]+)"', connection_string).group('ref')
        side_effect_mock = Mock()
        side_effect_mock.Metadata.Version = mock_infobase_version
        side_effect_mock.Metadata.Name = infobase_name
        return side_effect_mock
    external_connection_mock = Mock(side_effect=external_connection_mock_side_effect)
    type(mock_win32com_client_dispatch.return_value).Connect = external_connection_mock
    return external_connection_mock
