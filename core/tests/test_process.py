import logging
import random
from asyncio import TimeoutError
from unittest.mock import ANY, Mock

import pytest
from pytest_mock import MockerFixture

from core.exceptions import SubprocessException, V8Exception
from core.process import (
    _check_subprocess_return_code,
    _kill_process_emergency,
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


@pytest.mark.asyncio
async def test_kill_process_emergency_creates_subprocess(mock_asyncio_subprocess_succeeded):
    """
    `_kill_process_emergency` creates subprocess to try to kill process by pid
    """
    pid = random.randint(1000, 3000)
    await _kill_process_emergency(pid)
    mock_asyncio_subprocess_succeeded.assert_awaited_once()


@pytest.mark.asyncio
async def test_kill_process_emergency_logs_result_when_succeeded(caplog, mock_asyncio_subprocess_succeeded):
    """
    `_kill_process_emergency` logs result when successfully killed process by pid
    """
    pid = random.randint(1000, 3000)
    with caplog.at_level(logging.INFO):
        await _kill_process_emergency(pid)
    assert f"{pid} successfully killed" in caplog.text


@pytest.mark.asyncio
async def test_kill_process_emergency_logs_result_when_failed(caplog, mock_asyncio_subprocess_failed):
    """
    `_kill_process_emergency` logs result when failed to kill process by pid
    """
    pid = random.randint(1000, 3000)
    with caplog.at_level(logging.ERROR):
        await _kill_process_emergency(pid)
    assert f"{pid} was not killed" in caplog.text


@pytest.mark.asyncio
async def test_kill_process_emergency_logs_result_when_communication_error(
    caplog, mock_asyncio_subprocess_communication_error
):
    """
    `_kill_process_emergency` logs result when exception occurs
    """
    pid = random.randint(1000, 3000)
    with caplog.at_level(logging.ERROR):
        await _kill_process_emergency(pid)
    assert "Error while calling taskkill" in caplog.text


@pytest.mark.asyncio
async def test_execute_v8_command_pass_command_to_subprocess(
    mocker: MockerFixture, infobase, mock_asyncio_subprocess_succeeded, mock_cluster_com_controller
):
    """
    `execute_v8_command` pass command to create subprocess correctly
    """
    message = "test_message"
    command = "test_command"
    mocker.patch("core.utils.read_file_content", return_value=message)
    await execute_v8_command(infobase, command, "")
    mock_asyncio_subprocess_succeeded.assert_awaited_with(command)


@pytest.mark.asyncio
async def test_execute_v8_command_raises_if_nonzero_return_code(
    mocker: MockerFixture, infobase, mock_asyncio_subprocess_failed, mock_cluster_com_controller
):
    """
    `execute_v8_command` raises exception if subprocess returns non-zero return code
    """
    message = "test_message"
    command = "test_command"
    mocker.patch("core.utils.read_file_content", return_value=message)
    mocker.patch("core.process._kill_process_emergency")
    with pytest.raises(V8Exception):
        await execute_v8_command(infobase, command, "")


@pytest.mark.asyncio
async def test_execute_v8_command_passes_timeout_to_asyncio_wait_for(
    mocker: MockerFixture, infobase, mock_asyncio_subprocess_succeeded, mock_cluster_com_controller
):
    """
    `execute_v8_command` passes timeout value to `asyncio.wait_for`
    """
    message = "test_message"
    command = "test_command"
    timeout = 0.01
    mocker.patch("core.utils.read_file_content", return_value=message)
    mock_asyncio_wait_for = mocker.patch("asyncio.wait_for")
    await execute_v8_command(infobase, command, "", timeout=timeout)
    mock_asyncio_wait_for.assert_awaited_with(ANY, timeout=timeout)


@pytest.mark.asyncio
async def test_execute_v8_command_terminates_subprocess_when_timed_out(
    mocker: MockerFixture, infobase, mock_asyncio_subprocess_timeouted, mock_cluster_com_controller
):
    """
    `execute_v8_command` terminates subprocess when timed out
    """
    message = "test_message"
    command = "test_command"
    mocker.patch("core.utils.read_file_content", return_value=message)
    mocker.patch("asyncio.wait_for", side_effect=TimeoutError)
    mocker.patch("core.process._kill_process_emergency")
    await execute_v8_command(infobase, command, "")
    mock_asyncio_subprocess_timeouted.return_value.terminate.assert_awaited()


@pytest.mark.asyncio
async def test_execute_v8_command_calls_emergency_on_termination_error(
    mocker: MockerFixture, infobase, mock_asyncio_subprocess_termination_error, mock_cluster_com_controller
):
    """
    `execute_v8_command` calls `_kill_process_emergency` when got expection while terminating subprocess
    """
    message = "test_message"
    command = "test_command"
    mocker.patch("core.utils.read_file_content", return_value=message)
    mocker.patch("asyncio.wait_for", side_effect=TimeoutError)
    mock_kill_process_emergency = mocker.patch("core.process._kill_process_emergency")
    await execute_v8_command(infobase, command, "")
    mock_kill_process_emergency.assert_awaited()


@pytest.mark.asyncio
async def test_execute_v8_command_calls_emergency_on_communication_error(
    mocker: MockerFixture, infobase, mock_asyncio_subprocess_timeouted, mock_cluster_com_controller
):
    """
    `execute_v8_command` calls `_kill_process_emergency` when got expection while communicating with subprocess
    """
    message = "test_message"
    command = "test_command"
    mocker.patch("core.utils.read_file_content", return_value=message)
    mocker.patch("asyncio.wait_for", side_effect=Exception)
    mock_kill_process_emergency = mocker.patch("core.process._kill_process_emergency")
    await execute_v8_command(infobase, command, "")
    mock_kill_process_emergency.assert_awaited()


@pytest.mark.asyncio
async def test_execute_v8_command_locks_infobase_if_code_passed(
    mocker: MockerFixture, infobase, mock_asyncio_subprocess_succeeded, mock_cluster_com_controller
):
    """
    `execute_v8_command` locks infobase if permission code passed
    """
    message = "test_message"
    command = "test_command"
    permission_code = "test_permission_code"
    mocker.patch("core.utils.read_file_content", return_value=message)
    await execute_v8_command(infobase, command, "", permission_code)
    mock_cluster_com_controller.return_value.lock_info_base.assert_called_once()


@pytest.mark.asyncio
async def test_execute_v8_command_unlocks_infobase_if_code_passed(
    mocker: MockerFixture, infobase, mock_asyncio_subprocess_succeeded, mock_cluster_com_controller
):
    """
    `execute_v8_command` unlocks infobase if permission code passed
    """
    message = "test_message"
    command = "test_command"
    permission_code = "test_permission_code"
    mocker.patch("core.utils.read_file_content", return_value=message)
    await execute_v8_command(infobase, command, "", permission_code)
    mock_cluster_com_controller.return_value.unlock_info_base.assert_called_once()


@pytest.mark.asyncio
async def test_execute_v8_command_does_not_lock_infobase_if_code_is_none(
    mocker: MockerFixture, infobase, mock_asyncio_subprocess_succeeded, mock_cluster_com_controller
):
    """
    `execute_v8_command` does not lock infobase if permission code is none
    """
    message = "test_message"
    command = "test_command"
    mocker.patch("core.utils.read_file_content", return_value=message)
    await execute_v8_command(infobase, command, "")
    mock_cluster_com_controller.return_value.lock_info_base.assert_not_called()


@pytest.mark.asyncio
async def test_execute_v8_command_does_not_unlock_infobase_if_code_is_none(
    mocker: MockerFixture, infobase, mock_asyncio_subprocess_succeeded, mock_cluster_com_controller
):
    """
    `execute_v8_command` does not unlock infobase if permission code is none
    """
    message = "test_message"
    command = "test_command"
    mocker.patch("core.utils.read_file_content", return_value=message)
    await execute_v8_command(infobase, command, "")
    mock_cluster_com_controller.return_value.unlock_info_base.assert_not_called()


@pytest.mark.asyncio
async def test_execute_v8_command_terminates_infobase_sessions(
    mocker: MockerFixture, infobase, mock_asyncio_subprocess_succeeded, mock_cluster_com_controller
):
    """
    `execute_v8_command` terminates infobase sessions
    """
    message = "test_message"
    command = "test_command"
    mocker.patch("core.utils.read_file_content", return_value=message)
    await execute_v8_command(infobase, command, "")
    mock_cluster_com_controller.return_value.terminate_info_base_sessions.assert_called_once()


@pytest.mark.asyncio
async def test_execute_v8_sleeps_before_create_subprocess_if_parameter_passed(
    mocker: MockerFixture, infobase, mock_asyncio_subprocess_succeeded, mock_cluster_com_controller
):
    """
    `execute_v8_command` locks infobase if permission code passed
    """
    message = "test_message"
    command = "test_command"
    pause = 5.5
    mocker.patch("core.utils.read_file_content", return_value=message)
    aiosleep_mock = mocker.patch("asyncio.sleep")
    await execute_v8_command(infobase, command, "", create_subprocess_pause=pause)
    aiosleep_mock.assert_called_with(pause)


@pytest.mark.asyncio
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


@pytest.mark.asyncio
async def test_execute_subprocess_command_pass_env_to_subprocess(
    mocker: MockerFixture, infobase, mock_asyncio_subprocess_succeeded
):
    """
    `execute_subprocess_command` pass env to create subprocess correctly
    """
    message = "test_message"
    command = "test_command"
    env = {"test": "env"}
    mocker.patch("core.utils.read_file_content", return_value=message)
    await execute_subprocess_command(infobase, command, "", env=env)
    mock_asyncio_subprocess_succeeded.assert_awaited_with(command, env=env)


@pytest.mark.asyncio
async def test_execute_subprocess_command_passes_timeout_to_asyncio_wait_for(
    mocker: MockerFixture, infobase, mock_asyncio_subprocess_succeeded
):
    """
    `execute_subprocess_command` passes timeout value to `asyncio.wait_for`
    """
    message = "test_message"
    command = "test_command"
    timeout = 0.01
    mocker.patch("core.utils.read_file_content", return_value=message)
    mock_asyncio_wait_for = mocker.patch("asyncio.wait_for")
    await execute_subprocess_command(infobase, command, "", timeout=timeout)
    mock_asyncio_wait_for.assert_awaited_with(ANY, timeout=timeout)


@pytest.mark.asyncio
async def test_execute_subprocess_command_raises_if_nonzero_return_code(
    mocker: MockerFixture, infobase, mock_asyncio_subprocess_failed
):
    """
    `execute_subprocess_command` raises exception if subprocess returns non-zero return code
    """
    message = "test_message"
    command = "test_command"
    mocker.patch("core.utils.read_file_content", return_value=message)
    mocker.patch("core.process._kill_process_emergency")
    with pytest.raises(SubprocessException):
        await execute_subprocess_command(infobase, command, "")


@pytest.mark.asyncio
async def test_execute_subprocess_command_terminates_subprocess_when_timed_out(
    mocker: MockerFixture, infobase, mock_asyncio_subprocess_timeouted
):
    """
    `execute_subprocess_command` terminates subprocess when timed out
    """
    message = "test_message"
    command = "test_command"
    mocker.patch("core.utils.read_file_content", return_value=message)
    mocker.patch("asyncio.wait_for", side_effect=TimeoutError)
    mocker.patch("core.process._kill_process_emergency")
    await execute_subprocess_command(infobase, command, "")
    mock_asyncio_subprocess_timeouted.return_value.terminate.assert_awaited()


@pytest.mark.asyncio
async def test_execute_subprocess_command_calls_emergency_on_termination_error(
    mocker: MockerFixture, infobase, mock_asyncio_subprocess_termination_error
):
    """
    `execute_subprocess_command` calls `_kill_process_emergency` when got expection while terminating subprocess
    """
    message = "test_message"
    command = "test_command"
    mocker.patch("core.utils.read_file_content", return_value=message)
    mocker.patch("asyncio.wait_for", side_effect=TimeoutError)
    mock_kill_process_emergency = mocker.patch("core.process._kill_process_emergency")
    await execute_subprocess_command(infobase, command, "")
    mock_kill_process_emergency.assert_awaited()


@pytest.mark.asyncio
async def test_execute_subprocess_command_calls_emergency_on_communication_error(
    mocker: MockerFixture, infobase, mock_asyncio_subprocess_communication_error
):
    """
    `execute_subprocess_command` calls `_kill_process_emergency` when got expection while communicating with subprocess
    """
    message = "test_message"
    command = "test_command"
    mocker.patch("core.utils.read_file_content", return_value=message)
    mock_kill_process_emergency = mocker.patch("core.process._kill_process_emergency")
    await execute_subprocess_command(infobase, command, "")
    mock_kill_process_emergency.assert_awaited()
