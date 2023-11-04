import logging
from unittest.mock import Mock

import pytest
from pytest_mock import MockerFixture

from core.exceptions import SubprocessException, V8Exception
from core.process import (
    _check_subprocess_return_code,
    execute_subprocess_command,
    execute_v8_command,
)


def test_check_subprocess_return_code_raises_exception_when_subprocess_failed(mocker: MockerFixture, infobase):
    """
    `_check_subprocess_return_code` raises exception when failed
    """
    subprocess_mock = Mock()
    subprocess_mock.returncode = -1
    message = "test_message"
    mocker.patch("core.utils.read_file_content", return_value=message)
    with pytest.raises(SubprocessException):
        _check_subprocess_return_code(infobase, subprocess_mock, "", "", SubprocessException)


def test_check_subprocess_return_code_logs_message_when_subprocess_succeeded(mocker: MockerFixture, caplog, infobase):
    """
    `_check_subprocess_return_code` logs subprocess output when succeeded and log_output_on_success is True
    """
    subprocess_mock = Mock()
    subprocess_mock.returncode = 0
    message = "test_message"
    mocker.patch("core.utils.read_file_content", return_value=message)
    with caplog.at_level(logging.INFO):
        _check_subprocess_return_code(infobase, subprocess_mock, "", "", SubprocessException, True)
    assert message in caplog.text


def test_check_subprocess_return_code_does_not_logs_message_when_subprocess_succeeded_by_default(
    mocker: MockerFixture, caplog, infobase
):
    """
    `_check_subprocess_return_code` doesn't log subprocess output when succeeded by default
    """
    subprocess_mock = Mock()
    subprocess_mock.returncode = 0
    message = "test_message"
    mocker.patch("core.utils.read_file_content", return_value=message)
    with caplog.at_level(logging.INFO):
        _check_subprocess_return_code(infobase, subprocess_mock, "", "")
    assert message not in caplog.text


def test_check_subprocess_return_code_logs_message_when_subprocess_failed(mocker: MockerFixture, caplog, infobase):
    """
    `_check_subprocess_return_code` logs subprocess output when failed
    """
    subprocess_mock = Mock()
    subprocess_mock.returncode = -1
    message = "test_message"
    mocker.patch("core.utils.read_file_content", return_value=message)
    with caplog.at_level(logging.ERROR), pytest.raises(SubprocessException):
        _check_subprocess_return_code(infobase, subprocess_mock, "", "", SubprocessException)
    assert message in caplog.text


@pytest.mark.asyncio()
async def test_execute_v8_command_pass_command_to_subprocess(
    mocker: MockerFixture, infobase, mock_asyncio_subprocess_succeeded
):
    """
    `execute_v8_command` pass command to create subprocess correctly
    """
    message = "test_message"
    command = "test_command"
    mocker.patch("core.utils.read_file_content", return_value=message)
    mocker.patch("core.cluster.ClusterControlInterface", autospec=True)
    await execute_v8_command(infobase, command, "")
    mock_asyncio_subprocess_succeeded.assert_awaited_with(command)


@pytest.mark.asyncio()
async def test_execute_v8_command_raises_if_nonzero_return_code(
    mocker: MockerFixture, infobase, mock_asyncio_subprocess_failed
):
    """
    `execute_v8_command` raises exception if subprocess returns non-zero return code
    """
    message = "test_message"
    command = "test_command"
    mocker.patch("core.utils.read_file_content", return_value=message)
    mocker.patch("core.cluster.ClusterControlInterface", autospec=True)
    with pytest.raises(V8Exception):
        await execute_v8_command(infobase, command, "")


@pytest.mark.skip(reason="no clue how to create mock which can be timed out")
@pytest.mark.asyncio()
async def test_execute_v8_command_terminates_subprocess_when_timed_out(
    mocker: MockerFixture, infobase, mock_asyncio_subprocess_timeouted
):
    """
    `execute_v8_command` terminates subprocess when timed out
    """
    message = "test_message"
    command = "test_command"
    mocker.patch("core.utils.read_file_content", return_value=message)
    mocker.patch("core.cluster.ClusterControlInterface", autospec=True)
    await execute_v8_command(infobase, command, "", timeout=0.01)
    mock_asyncio_subprocess_timeouted.terminate.assert_awaited()


@pytest.mark.asyncio()
async def test_execute_v8_command_locks_infobase_if_code_passed(
    mocker: MockerFixture, infobase, mock_asyncio_subprocess_succeeded
):
    """
    `execute_v8_command` locks infobase if permission code passed
    """
    message = "test_message"
    command = "test_command"
    permission_code = "test_permission_code"
    mocker.patch("core.utils.read_file_content", return_value=message)
    cci_mock = mocker.patch("core.cluster.ClusterControlInterface", autospec=True)
    await execute_v8_command(infobase, command, "", permission_code)
    cci_mock.return_value.__enter__.return_value.lock_info_base.assert_called_once()


@pytest.mark.asyncio()
async def test_execute_v8_command_unlocks_infobase_if_code_passed(
    mocker: MockerFixture, infobase, mock_asyncio_subprocess_succeeded
):
    """
    `execute_v8_command` unlocks infobase if permission code passed
    """
    message = "test_message"
    command = "test_command"
    permission_code = "test_permission_code"
    mocker.patch("core.utils.read_file_content", return_value=message)
    cci_mock = mocker.patch("core.cluster.ClusterControlInterface", autospec=True)
    await execute_v8_command(infobase, command, "", permission_code)
    cci_mock.return_value.__enter__.return_value.unlock_info_base.assert_called_once()


@pytest.mark.asyncio()
async def test_execute_subprocess_command_pass_command_to_subprocess(
    mocker: MockerFixture, infobase, mock_asyncio_subprocess_succeeded
):
    """
    `execute_subprocess_command` pass command to create subprocess correctly
    """
    message = "test_message"
    command = "test_command"
    mocker.patch("core.utils.read_file_content", return_value=message)
    await execute_subprocess_command(infobase, command, "")
    mock_asyncio_subprocess_succeeded.assert_awaited_with(command)


@pytest.mark.asyncio()
async def test_execute_subprocess_command_pass_env_to_subprocess(
    mocker: MockerFixture, infobase, mock_asyncio_subprocess_succeeded
):
    """
    `execute_subprocess_command` pass command to create subprocess correctly
    """
    message = "test_message"
    command = "test_command"
    env = {"test": "env"}
    mocker.patch("core.utils.read_file_content", return_value=message)
    await execute_subprocess_command(infobase, command, "", env=env)
    mock_asyncio_subprocess_succeeded.assert_awaited_with(command, env=env)


@pytest.mark.asyncio()
async def test_execute_subprocess_command_raises_if_nonzero_return_code(
    mocker: MockerFixture, infobase, mock_asyncio_subprocess_failed
):
    """
    `execute_subprocess_command` raises exception if subprocess returns non-zero return code
    """
    message = "test_message"
    command = "test_command"
    mocker.patch("core.utils.read_file_content", return_value=message)
    with pytest.raises(SubprocessException):
        await execute_subprocess_command(infobase, command, "")


@pytest.mark.skip(reason="no clue how to create mock which can be timed out")
@pytest.mark.asyncio()
async def test_execute_subprocess_command_terminates_subprocess_when_timed_out(
    mocker: MockerFixture, infobase, mock_asyncio_subprocess_timeouted
):
    """
    `execute_subprocess_command` terminates subprocess when timed out
    """
    message = "test_message"
    command = "test_command"
    mocker.patch("core.utils.read_file_content", return_value=message)
    await execute_subprocess_command(infobase, command, "", timeout=0.01)
    mock_asyncio_subprocess_timeouted.terminate.assert_awaited()
