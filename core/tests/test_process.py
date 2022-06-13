from unittest.mock import MagicMock
import pytest
from pytest_mock import MockerFixture

from core.exceptions import V8Exception
from core.process import execute_v8_command


@pytest.mark.asyncio
async def test_execute_v8_command_pass_command_to_subprocess(
    mocker: MockerFixture, 
    infobase, 
    mock_asyncio_subprocess_succeeded
):
    """
    `execute_v8_command` pass command to create subprocess correctly
    """
    message = 'test_message'
    command = 'test_command'
    mocker.patch('core.utils.read_file_content', return_value=message)
    mocker.patch('core.process.ClusterControlInterface', autospec=True)
    await execute_v8_command(infobase, command, '')
    mock_asyncio_subprocess_succeeded.assert_awaited_with(command)


@pytest.mark.asyncio
async def test_execute_v8_command_raises_if_nonzero_return_code(
    mocker: MockerFixture, 
    infobase, 
    mock_asyncio_subprocess_failed
):
    """
    `execute_v8_command` raises exception if subprocess returns non-zero return code
    """
    message = 'test_message'
    command = 'test_command'
    mocker.patch('core.utils.read_file_content', return_value=message)
    mocker.patch('core.process.ClusterControlInterface', autospec=True)
    with pytest.raises(V8Exception):
        await execute_v8_command(infobase, command, '')


@pytest.mark.skip(reason='no clue how to create mock which can be timed out')
@pytest.mark.asyncio
async def test_execute_v8_command_terminates_subprocess_when_timed_out(
    mocker: MockerFixture, 
    infobase, 
    mock_asyncio_subprocess_timeouted
):
    """
    `execute_v8_command` terminates subprocess when timed out
    """
    message = 'test_message'
    command = 'test_command'
    mocker.patch('core.utils.read_file_content', return_value=message)
    mocker.patch('core.process.ClusterControlInterface', autospec=True)
    await execute_v8_command(infobase, command, '', timeout=0.01)
    mock_asyncio_subprocess_timeouted.terminate.assert_awaited()


@pytest.mark.asyncio
async def test_execute_v8_command_locks_infobase_if_code_passed(
    mocker: MockerFixture, 
    infobase, 
    mock_asyncio_subprocess_succeeded
):
    """
    `execute_v8_command` locks infobase if permission code passed
    """
    message = 'test_message'
    command = 'test_command'
    permission_code = 'test_permission_code'
    mocker.patch('core.utils.read_file_content', return_value=message)
    cci_mock = mocker.patch('core.process.ClusterControlInterface', autospec=True)
    await execute_v8_command(infobase, command, '', permission_code)
    cci_mock.return_value.__enter__.return_value.lock_info_base.assert_called_once()


@pytest.mark.asyncio
async def test_execute_v8_command_unlocks_infobase_if_code_passed(
    mocker: MockerFixture, 
    infobase, 
    mock_asyncio_subprocess_succeeded
):
    """
    `execute_v8_command` unlocks infobase if permission code passed
    """
    message = 'test_message'
    command = 'test_command'
    permission_code = 'test_permission_code'
    mocker.patch('core.utils.read_file_content', return_value=message)
    cci_mock = mocker.patch('core.process.ClusterControlInterface', autospec=True)
    await execute_v8_command(infobase, command, '', permission_code)
    cci_mock.return_value.__enter__.return_value.unlock_info_base.assert_called_once()
