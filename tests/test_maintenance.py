import pytest
from pytest_mock import MockerFixture

from maintenance import rotate_logs, _maintenance_v8


@pytest.mark.asyncio
async def test_rotate_logs_calls_inner_func(mocker: MockerFixture, infobase):
    """
    `rotate_logs` calls `remove_old_files_by_pattern` for rotating logs
    """
    remove_old_files_mock = mocker.patch('core.utils.remove_old_files_by_pattern')
    await rotate_logs(infobase)
    remove_old_files_mock.assert_awaited()


@pytest.mark.asyncio
async def test_maintenance_v8_calls_execute_v8_command(mocker: MockerFixture, infobase, mock_get_platform_full_path):
    """
    `_maintenance_v8` calls execute_v8_command to run created command
    """
    execute_v8_command_mock = mocker.patch('maintenance.execute_v8_command')
    await _maintenance_v8(infobase)
    execute_v8_command_mock.assert_awaited()
