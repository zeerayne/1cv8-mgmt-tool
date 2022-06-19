import pytest
from pytest_mock import MockerFixture

from maintenance import rotate_logs


@pytest.mark.asyncio
async def test_rotate_logs_calls_inner_func(mocker: MockerFixture, infobase):
    """
    `rotate_logs` calls `remove_old_files_by_pattern` for rotating logs
    """
    remove_old_files_mock = mocker.patch('core.utils.remove_old_files_by_pattern')
    await rotate_logs(infobase)
    remove_old_files_mock.assert_awaited()
