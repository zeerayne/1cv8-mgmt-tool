from unittest.mock import AsyncMock, PropertyMock

import pytest
from pytest_mock import MockerFixture

import core.types as core_types

from backup import replicate_backup, rotate_backups, _backup_v8, _backup_pgdump
from core.exceptions import V8Exception


@pytest.mark.asyncio
async def test_replicate_backup_replicate_to_every_path(mocker: MockerFixture):
    """
    Backup replicates to every replication path
    """
    backup_file_path = 'test/backup.filename'
    replication_paths = ['test/replication/path/01', 'test/replication/path/02']
    mocker.patch('pathlib.Path')
    aiocopyfile_mock = mocker.patch('aioshutil.copyfile', return_value=AsyncMock())
    await replicate_backup(backup_file_path, replication_paths)
    assert aiocopyfile_mock.await_count == len(replication_paths)


@pytest.mark.asyncio
async def test_replicate_backup_does_nothing_when_empty_paths(mocker: MockerFixture):
    """
    Backup replication does nothing when nowhere to replicate
    """
    backup_file_path = 'test/backup.filename'
    replication_paths = []
    mocker.patch('pathlib.Path')
    aiocopyfile_mock = mocker.patch('aioshutil.copyfile', return_value=AsyncMock())
    await replicate_backup(backup_file_path, replication_paths)
    aiocopyfile_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_rotate_backups_calls_old_file_remover(mocker: MockerFixture, infobase):
    """
    Backup rotation calls `remove_old_files_by_pattern` function
    """
    remove_old_mock = mocker.patch('core.utils.remove_old_files_by_pattern', return_value=AsyncMock())
    await rotate_backups(infobase)
    remove_old_mock.assert_awaited()


@pytest.mark.asyncio
async def test_rotate_backups_calls_old_file_remover_for_replication_paths(mocker: MockerFixture, infobase):
    """
    Backup rotation calls `remove_old_files_by_pattern` function for every replication path
    """
    replication_paths = ['test/replication/path/01', 'test/replication/path/02']
    mocker.patch('conf.settings.BACKUP_REPLICATION_ENABLED', new_callable=PropertyMock(return_value=True))
    mocker.patch('conf.settings.BACKUP_REPLICATION_PATHS', new_callable=PropertyMock(return_value=replication_paths))
    remove_old_mock = mocker.patch('core.utils.remove_old_files_by_pattern', return_value=AsyncMock())
    await rotate_backups(infobase)
    assert remove_old_mock.await_count == len(replication_paths) + 1  # plus one for initial backup place

@pytest.mark.asyncio
async def test_backup_v8_calls_execute_v8_command(mocker: MockerFixture, infobase):
    """
    Backup with 1cv8 tools calls `execute_v8_command`
    """
    mocker.patch('core.utils.get_platform_full_path', return_value='')
    execute_v8_mock = mocker.patch('backup.execute_v8_command', return_value=AsyncMock())
    await _backup_v8(infobase)
    execute_v8_mock.assert_awaited()


@pytest.mark.asyncio
async def test_backup_v8_make_retries(mocker: MockerFixture, infobase):
    """
    Backup with 1cv8 tools makes retries according to retry policy
    """
    backup_retries = 1
    mocker.patch('core.utils.get_platform_full_path', return_value='')
    mocker.patch('conf.settings.BACKUP_RETRIES_V8', new_callable=PropertyMock(return_value=backup_retries))
    execute_v8_mock = mocker.patch('backup.execute_v8_command', side_effect=V8Exception)
    await _backup_v8(infobase)
    execute_v8_mock.await_count == backup_retries + 1  # plus one for initial call


@pytest.mark.asyncio
async def test_backup_v8_return_backup_result_type_object_when_succeeded(mocker: MockerFixture, infobase):
    """
    Backup with 1cv8 tools returns object of type `InfoBaseBackupTaskResult` when succeeded
    """
    mocker.patch('core.utils.get_platform_full_path', return_value='')
    mocker.patch('backup.execute_v8_command', return_value=AsyncMock())
    result = await _backup_v8(infobase)
    assert isinstance(result, core_types.InfoBaseBackupTaskResult)


@pytest.mark.asyncio
async def test_backup_v8_return_backup_result_type_object_when_failed(mocker: MockerFixture, infobase):
    """
    Backup with 1cv8 tools returns object of type `InfoBaseBackupTaskResult` when failed
    """
    mocker.patch('core.utils.get_platform_full_path', return_value='')
    mocker.patch('backup.execute_v8_command', side_effect=V8Exception)
    result = await _backup_v8(infobase)
    assert isinstance(result, core_types.InfoBaseBackupTaskResult)


@pytest.mark.asyncio
async def test_backup_v8_return_backup_result_succeeded_true_when_succeeded(mocker: MockerFixture, infobase):
    """
    Backup with 1cv8 tools returns object with succeeded == True when succeeded
    """
    mocker.patch('core.utils.get_platform_full_path', return_value='')
    mocker.patch('backup.execute_v8_command', return_value=AsyncMock())
    result = await _backup_v8(infobase)
    assert result.succeeded == True


@pytest.mark.asyncio
async def test_backup_v8_return_backup_result_succeeded_true_when_failed(mocker: MockerFixture, infobase):
    """
    Backup with 1cv8 tools returns object with succeeded == False when failed
    """
    mocker.patch('core.utils.get_platform_full_path', return_value='')
    mocker.patch('backup.execute_v8_command', side_effect=V8Exception)
    result = await _backup_v8(infobase)
    assert result.succeeded == False
