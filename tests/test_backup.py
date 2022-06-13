from unittest.mock import AsyncMock, PropertyMock

import pytest
from pytest_mock import MockerFixture

from backup import replicate_backup, rotate_backups


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
