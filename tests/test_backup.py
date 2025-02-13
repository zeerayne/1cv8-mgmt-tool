import asyncio
import logging
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, PropertyMock

import pytest
from pytest_mock import MockerFixture

import core.models as core_models
from backup import (
    _backup_info_base,
    _backup_pgdump,
    _backup_v8,
    analyze_results,
    backup_info_base,
    create_aws_upload_task,
    create_backup_replication_task,
    replicate_backup,
    replicate_info_base,
    rotate_backups,
    send_email_notification,
)
from conf import settings
from core.exceptions import SubprocessException, V8Exception


@pytest.mark.asyncio
async def test_replicate_backup_replicate_to_every_path(mocker: MockerFixture):
    """
    Backup replicates to every replication path
    """
    backup_file_path = "test/backup.filename"
    replication_paths = ["test/replication/path/01", "test/replication/path/02"]
    mocker.patch("pathlib.Path")
    aiocopyfile_mock = mocker.patch("aioshutil.copyfile", return_value=AsyncMock())
    await replicate_backup(backup_file_path, replication_paths)
    assert aiocopyfile_mock.await_count == len(replication_paths)


@pytest.mark.asyncio
async def test_replicate_backup_replicate_log_exception_when_failed(mocker: MockerFixture, caplog):
    """
    `replicate_backup` logs exception when failed
    """
    backup_file_path = "test/backup.filename"
    replication_paths = ["test/replication/path/01", "test/replication/path/02"]
    mocker.patch("pathlib.Path")
    mocker.patch("aioshutil.copyfile", side_effect=Exception)
    with caplog.at_level(logging.ERROR):
        await replicate_backup(backup_file_path, replication_paths)
    assert "Problems while replicating" in caplog.text


@pytest.mark.asyncio
async def test_replicate_backup_does_nothing_when_empty_paths(mocker: MockerFixture):
    """
    Backup replication does nothing when nowhere to replicate
    """
    backup_file_path = "test/backup.filename"
    replication_paths = []
    mocker.patch("pathlib.Path")
    aiocopyfile_mock = mocker.patch("aioshutil.copyfile", return_value=AsyncMock())
    await replicate_backup(backup_file_path, replication_paths)
    aiocopyfile_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_rotate_backups_calls_old_file_remover(mocker: MockerFixture, infobase):
    """
    Backup rotation calls `remove_old_files_by_pattern` function
    """
    remove_old_mock = mocker.patch("core.utils.remove_old_files_by_pattern", return_value=AsyncMock())
    await rotate_backups(infobase)
    remove_old_mock.assert_awaited()


@pytest.mark.asyncio
async def test_rotate_backups_calls_old_file_remover_for_replication_paths(mocker: MockerFixture, infobase):
    """
    Backup rotation calls `remove_old_files_by_pattern` function for every replication path
    """
    replication_paths = ["test/replication/path/01", "test/replication/path/02"]
    mocker.patch("conf.settings.BACKUP_REPLICATION", new_callable=PropertyMock(return_value=True))
    mocker.patch(
        "conf.settings.BACKUP_REPLICATION_PATHS",
        new_callable=PropertyMock(return_value=replication_paths),
    )
    remove_old_mock = mocker.patch("core.utils.remove_old_files_by_pattern", return_value=AsyncMock())
    await rotate_backups(infobase)
    assert remove_old_mock.await_count == len(replication_paths) + 1  # plus one for initial backup place


@pytest.mark.asyncio
async def test_backup_v8_calls_execute_v8_command(mocker: MockerFixture, infobase, mock_get_1cv8_service_full_path):
    """
    Backup with 1cv8 tools calls `execute_v8_command`
    """
    execute_v8_mock = mocker.patch("backup.execute_v8_command", return_value=AsyncMock())
    await _backup_v8(infobase)
    execute_v8_mock.assert_awaited()


@pytest.mark.asyncio
async def test_backup_v8_makes_retries(mocker: MockerFixture, infobase, mock_get_1cv8_service_full_path):
    """
    Backup with 1cv8 tools makes retries according to retry policy
    """
    backup_retries = 1
    mocker.patch(
        "conf.settings.BACKUP_RETRIES_V8",
        new_callable=PropertyMock(return_value=backup_retries),
    )
    execute_v8_mock = mocker.patch("backup.execute_v8_command", side_effect=V8Exception)
    await _backup_v8(infobase)
    assert execute_v8_mock.await_count == backup_retries + 1  # plus one for initial call


@pytest.mark.asyncio
async def test_backup_v8_return_backup_result_type_object_when_succeeded(
    mocker: MockerFixture, infobase, mock_get_1cv8_service_full_path
):
    """
    Backup with 1cv8 tools returns object of type `InfoBaseBackupTaskResult` when succeeded
    """
    mocker.patch("backup.execute_v8_command", return_value=AsyncMock())
    result = await _backup_v8(infobase)
    assert isinstance(result, core_models.InfoBaseBackupTaskResult)


@pytest.mark.asyncio
async def test_backup_v8_return_backup_result_type_object_when_failed(
    mocker: MockerFixture, infobase, mock_get_1cv8_service_full_path
):
    """
    Backup with 1cv8 tools returns object of type `InfoBaseBackupTaskResult` when failed
    """
    mocker.patch("backup.execute_v8_command", side_effect=V8Exception)
    result = await _backup_v8(infobase)
    assert isinstance(result, core_models.InfoBaseBackupTaskResult)


@pytest.mark.asyncio
async def test_backup_v8_return_result_for_exact_infobase_when_succeeded(
    mocker: MockerFixture, infobase, mock_get_1cv8_service_full_path
):
    """
    Backup with 1cv8 tools returns object for exact infobase which was provided when succeeded
    """
    mocker.patch("backup.execute_v8_command", return_value=AsyncMock())
    result = await _backup_v8(infobase)
    assert result.infobase_name == infobase


@pytest.mark.asyncio
async def test_backup_v8_return_backup_result_succeeded_true_when_succeeded(
    mocker: MockerFixture, infobase, mock_get_1cv8_service_full_path
):
    """
    Backup with 1cv8 tools returns object with succeeded is True when succeeded
    """
    mocker.patch("backup.execute_v8_command", return_value=AsyncMock())
    result = await _backup_v8(infobase)
    assert result.succeeded is True


@pytest.mark.asyncio
async def test_backup_v8_return_result_for_exact_infobase_when_failed(
    mocker: MockerFixture, infobase, mock_get_1cv8_service_full_path
):
    """
    Backup with 1cv8 tools returns object for exact infobase which was provided when faild
    """
    mocker.patch("backup.execute_v8_command", side_effect=V8Exception)
    result = await _backup_v8(infobase)
    assert result.infobase_name == infobase


@pytest.mark.asyncio
async def test_backup_v8_return_backup_result_succeeded_false_when_failed(
    mocker: MockerFixture, infobase, mock_get_1cv8_service_full_path
):
    """
    Backup with 1cv8 tools returns object with succeeded is False when failed
    """
    mocker.patch("backup.execute_v8_command", side_effect=V8Exception)
    result = await _backup_v8(infobase)
    assert result.succeeded is False


@pytest.mark.asyncio
async def test_backup_pgdump_calls_execute_subprocess_command(
    mocker: MockerFixture,
    infobase,
    mock_prepare_postgres_connection_vars,
    mock_get_postgres_version_16,
):
    """
    Backup with pgdump calls `execute_subprocess_command`
    """
    execute_subprocess_mock = mocker.patch("backup.execute_subprocess_command", return_value=AsyncMock())
    await _backup_pgdump(infobase, "", "", "")
    execute_subprocess_mock.assert_awaited()


@pytest.mark.asyncio
async def test_backup_pgdump_makes_retries(
    mocker: MockerFixture,
    infobase,
    mock_get_1cv8_service_full_path,
    mock_prepare_postgres_connection_vars,
    mock_get_postgres_version_16,
):
    """
    Backup with pgdump makes retries according to retry policy
    """
    backup_retries = 1
    mocker.patch(
        "conf.settings.BACKUP_RETRIES_PG",
        new_callable=PropertyMock(return_value=backup_retries),
    )
    execute_subprocess_mock = mocker.patch("backup.execute_subprocess_command", side_effect=SubprocessException)
    await _backup_pgdump(infobase, "", "", "")
    assert execute_subprocess_mock.await_count == backup_retries + 1  # plus one for initial call


@pytest.mark.asyncio
async def test_backup_pgdump_return_backup_result_type_object_when_succeeded(
    mocker: MockerFixture,
    infobase,
    mock_get_1cv8_service_full_path,
    mock_prepare_postgres_connection_vars,
    mock_get_postgres_version_16,
):
    """
    Backup with pgdump returns object of type `InfoBaseBackupTaskResult` when succeeded
    """
    mocker.patch("backup.execute_subprocess_command", return_value=AsyncMock())
    result = await _backup_pgdump(infobase, "", "", "")
    assert isinstance(result, core_models.InfoBaseBackupTaskResult)


@pytest.mark.asyncio
async def test_backup_pgdump_return_backup_result_type_object_when_failed(
    mocker: MockerFixture,
    infobase,
    mock_get_1cv8_service_full_path,
    mock_prepare_postgres_connection_vars,
    mock_get_postgres_version_16,
):
    """
    Backup with pgdump returns object of type `InfoBaseBackupTaskResult` when failed
    """
    mocker.patch("backup.execute_subprocess_command", side_effect=SubprocessException)
    result = await _backup_pgdump(infobase, "", "", "")
    assert isinstance(result, core_models.InfoBaseBackupTaskResult)


@pytest.mark.asyncio
async def test_backup_pgdump_return_backup_result_succeeded_true_when_succeeded(
    mocker: MockerFixture,
    infobase,
    mock_get_1cv8_service_full_path,
    mock_prepare_postgres_connection_vars,
    mock_get_postgres_version_16,
):
    """
    Backup with pgdump returns object with succeeded is True when succeeded
    """
    mocker.patch("backup.execute_subprocess_command", return_value=AsyncMock())
    result = await _backup_pgdump(infobase, "", "", "")
    assert result.succeeded is True


@pytest.mark.asyncio
async def test_backup_pgdump_return_backup_result_succeeded_false_when_failed(
    mocker: MockerFixture,
    infobase,
    mock_get_1cv8_service_full_path,
    mock_prepare_postgres_connection_vars,
    mock_get_postgres_version_16,
):
    """
    Backup with pgdump returns object with succeeded is False when failed
    """
    mocker.patch("backup.execute_subprocess_command", side_effect=SubprocessException)
    result = await _backup_pgdump(infobase, "", "", "")
    assert result.succeeded is False


@pytest.mark.asyncio
async def test_backup_pgdump_return_result_for_exact_infobase_when_succeeded(
    mocker: MockerFixture,
    infobase,
    mock_get_1cv8_service_full_path,
    mock_prepare_postgres_connection_vars,
    mock_get_postgres_version_16,
):
    """
    Backup with pgdump returns object for exact infobase which was provided when succeeded
    """
    mocker.patch("backup.execute_subprocess_command", return_value=AsyncMock())
    result = await _backup_pgdump(infobase, "", "", "")
    assert result.infobase_name == infobase


@pytest.mark.asyncio
async def test_backup_pgdump_return_result_for_exact_infobase_when_failed(
    mocker: MockerFixture,
    infobase,
    mock_get_1cv8_service_full_path,
    mock_prepare_postgres_connection_vars,
    mock_get_postgres_version_16,
):
    """
    Backup with pgdump returns object for exact infobase which was provided when failed
    """
    mocker.patch("backup.execute_subprocess_command", side_effect=SubprocessException)
    result = await _backup_pgdump(infobase, "", "", "")
    assert result.infobase_name == infobase


@pytest.mark.asyncio
async def test_backup_pgdump_return_negative_result_when_failed(
    mocker: MockerFixture,
    infobase,
    mock_get_1cv8_service_full_path,
    mock_prepare_postgres_connection_vars,
    mock_get_postgres_version_16,
):
    """
    Backup with pgdump returns object with `succeeded == False` when failed
    """
    mocker.patch("backup.execute_subprocess_command", side_effect=SubprocessException)
    result = await _backup_pgdump(infobase, "", "", "")
    assert result.succeeded is False


@pytest.mark.asyncio
async def test_backup_pgdump_return_result_for_exact_infobase_when_failed_to_find_creds(
    mocker: MockerFixture,
    infobase,
):
    """
    Backup with pgdump returns object for exact infobase which was provided when failed to find db credentials
    """
    mocker.patch("utils.postgres.prepare_postgres_connection_vars", side_effect=KeyError)
    result = await _backup_pgdump(infobase, "", "", "")
    assert result.infobase_name == infobase


@pytest.mark.asyncio
async def test_backup_pgdump_return_negative_result_when_failed_to_find_creds(
    mocker: MockerFixture,
    infobase,
):
    """
    Backup with pgdump returns object with `succeeded == False` when failed to find db credentials
    """
    mocker.patch("utils.postgres.prepare_postgres_connection_vars", side_effect=KeyError)
    result = await _backup_pgdump(infobase, "", "", "")
    assert result.succeeded is False


@pytest.mark.asyncio
async def test_backup_info_base_run_v8_backup(mocker: MockerFixture, mock_cluster_com_controller, infobase):
    """
    `_backup_info_base` calls `_backup_v8` by default
    """
    com_func_wrapper_mock = mocker.patch("core.cluster.utils.com_func_wrapper")
    await _backup_info_base(infobase)
    com_func_wrapper_mock.assert_awaited_with(_backup_v8, infobase)


@pytest.mark.asyncio
async def test_backup_info_base_run_v8_backup_when_pgbackup_is_enabled_and_dbms_is_not_postgres(
    mocker: MockerFixture, infobase, mock_cluster_mssql_infobase
):
    """
    `_backup_info_base` calls `_backup_v8` if BACKUP_PG is True, but infobase DBMS is not postgres
    """
    mocker.patch("conf.settings.BACKUP_PG", new_callable=PropertyMock(return_value=True))
    com_func_wrapper_mock = mocker.patch("core.cluster.utils.com_func_wrapper")
    await _backup_info_base(infobase)
    com_func_wrapper_mock.assert_awaited_with(_backup_v8, infobase)


@pytest.mark.asyncio
async def test_backup_info_base_run_pgdump_backup_when_pgbackup_is_enabled_and_dbms_is_postgres(
    mocker: MockerFixture, infobase, mock_cluster_postgres_infobase
):
    """
    `_backup_info_base` calls `_backup_pgdump` if BACKUP_PG is True, and infobase DBMS is postgres
    """
    db_server, db_name, db_user = mock_cluster_postgres_infobase
    mocker.patch("conf.settings.BACKUP_PG", new_callable=PropertyMock(return_value=True))
    backup_pgdump_mock = mocker.patch("backup._backup_pgdump")
    await _backup_info_base(infobase)
    backup_pgdump_mock.assert_awaited_with(infobase, db_server, db_name, db_user)


@pytest.mark.asyncio
async def test_backup_info_base_returns_value_from_v8_backup(
    mocker: MockerFixture, mock_cluster_com_controller, infobase
):
    """
    `_backup_info_base` returns value from underlying `com_func_wrapper` function
    """
    value = core_models.InfoBaseBackupTaskResult(infobase, True, "")
    mocker.patch("core.cluster.utils.com_func_wrapper", return_value=value)
    result = await _backup_info_base(infobase)
    assert result == value


@pytest.mark.asyncio
async def test_backup_info_base_returns_value_from_pgdump_backup(
    mocker: MockerFixture, infobase, mock_cluster_postgres_infobase
):
    """
    `_backup_info_base` returns value from underlying `_backup_pgdump` function
    """
    value = core_models.InfoBaseBackupTaskResult(infobase, True, "")
    mocker.patch("conf.settings.BACKUP_PG", new_callable=PropertyMock(return_value=True))
    mocker.patch("backup._backup_pgdump", return_value=value)
    result = await _backup_info_base(infobase)
    assert result == value


@pytest.mark.asyncio
async def test_backup_info_calls_inner_func(mocker: MockerFixture, infobase):
    """
    `backup_info_base` calls inner backup function
    """
    mocker.patch("backup.rotate_backups")
    inner_func_mock = mocker.patch("backup._backup_info_base")
    await backup_info_base(infobase, asyncio.Semaphore(1))
    inner_func_mock.assert_awaited_with(infobase)


@pytest.mark.asyncio
async def test_backup_info_calls_rotate_backups(mocker: MockerFixture, infobase):
    """
    `backup_info_base` calls `rotate_backups`
    """
    mocker.patch("backup._backup_info_base")
    rotate_backups_mock = mocker.patch("backup.rotate_backups")
    await backup_info_base(infobase, asyncio.Semaphore(1))
    rotate_backups_mock.assert_awaited_with(infobase)


@pytest.mark.asyncio
async def test_backup_info_dont_calls_replicate_backup_if_replication_is_enabled_and_backup_failed(
    mocker: MockerFixture, infobase
):
    """
    `backup_info_base` don't calls `replicate_backup` if BACKUP_REPLICATION is True and backup failed
    """
    value = core_models.InfoBaseBackupTaskResult(infobase, False)
    mocker.patch("backup.rotate_backups")
    mocker.patch("backup._backup_info_base", return_value=value)
    mocker.patch("conf.settings.BACKUP_REPLICATION", new_callable=PropertyMock(return_value=True))
    replicate_backup_mock = mocker.patch("backup.replicate_backup")
    await backup_info_base(infobase, asyncio.Semaphore(1))
    replicate_backup_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_backup_info_returns_value_from_inner_func(mocker: MockerFixture, infobase):
    """
    `backup_info_base` returns value from inner backup function
    """
    value = core_models.InfoBaseBackupTaskResult(infobase, True, "test/backup.path")
    mocker.patch("backup._backup_info_base", return_value=value)
    mocker.patch("backup.rotate_backups")
    result = await backup_info_base(infobase, asyncio.Semaphore(1))
    assert result == value


@pytest.mark.asyncio
async def test_backup_info_returns_false_result_if_inner_func_fails(mocker: MockerFixture, infobase):
    """
    `backup_info_base` returns succeeded is False result if inner backup function fails
    """
    mocker.patch("backup._backup_info_base", side_effect=Exception)
    mocker.patch("backup.rotate_backups")
    result = await backup_info_base(infobase, asyncio.Semaphore(1))
    assert result.succeeded is False


@pytest.mark.asyncio
async def test_backup_info_returns_value_from_inner_func_if_rotate_backups_fails(mocker: MockerFixture, infobase):
    """
    `backup_info_base` returns value from inner backup function if `rotate_backups` fails
    """
    value = core_models.InfoBaseBackupTaskResult(infobase, True, "test/backup.path")
    mocker.patch("backup._backup_info_base", return_value=value)
    mocker.patch("backup.rotate_backups", side_effect=Exception)
    result = await backup_info_base(infobase, asyncio.Semaphore(1))
    assert result == value


@pytest.mark.asyncio
async def test_replicate_info_base_calls_replicate_backup_if_replication_is_enabled_and_backup_was_successfull(
    mocker: MockerFixture, infobase
):
    """
    `replicate_info_base` calls `replicate_backup` if BACKUP_REPLICATION is True and backup was successfull
    """
    backup_path = "test/backup.path"
    value = core_models.InfoBaseBackupTaskResult(infobase, True, backup_path)
    replicate_backup_mock = mocker.patch("backup.replicate_backup")
    mocker.patch("conf.settings.BACKUP_REPLICATION", new_callable=PropertyMock(return_value=True))
    await replicate_info_base(value, asyncio.Semaphore(1))
    replicate_backup_mock.assert_awaited_with(value.backup_filename, settings.BACKUP_REPLICATION_PATHS)


@pytest.mark.asyncio
async def test_replicate_info_base_logs_exception_if_replicate_backup_fails(mocker: MockerFixture, caplog, infobase):
    """
    `replicate_info_base` logs exception if `replicate_backup` fails
    """
    value = core_models.InfoBaseBackupTaskResult(infobase, True, "test/backup.path")
    mocker.patch("conf.settings.BACKUP_REPLICATION", new_callable=PropertyMock(return_value=True))
    mocker.patch("backup.replicate_backup", side_effect=Exception)
    with caplog.at_level(logging.ERROR):
        await replicate_info_base(value, asyncio.Semaphore(1))
    assert "exception occurred in `replicate_backup`" in caplog.text


def test_analyze_results_calls_backup_analyze(mocker: MockerFixture, infobases, mixed_backup_result):
    """
    `analyze_results` calls `analyze_backup_result` by default
    """
    datetime_start = datetime.now()
    datetime_finish = datetime_start + timedelta(minutes=5)
    analyze_backup_result_mock = mocker.patch("backup.analyze_backup_result")
    analyze_results(
        infobases,
        mixed_backup_result,
        datetime_start,
        datetime_finish,
        None,
        None,
        None,
    )
    analyze_backup_result_mock.assert_called_with(mixed_backup_result, infobases, datetime_start, datetime_finish)


def test_analyze_results_calls_backup_analyze_if_aws_enabled(
    mocker: MockerFixture, infobases, mixed_backup_result, mixed_aws_result
):
    """
    `analyze_results` calls `analyze_backup_result` if AWS_ENABLED is True
    """
    backup_datetime_start = datetime.now()
    backup_datetime_finish = backup_datetime_start + timedelta(minutes=5)
    aws_datetime_start = datetime.now()
    aws_datetime_finish = aws_datetime_start + timedelta(minutes=5)
    mocker.patch("conf.settings.AWS_ENABLED", new_callable=PropertyMock(return_value=True))
    mocker.patch("backup.analyze_s3_result")
    analyze_backup_result_mock = mocker.patch("backup.analyze_backup_result")
    analyze_results(
        infobases,
        mixed_backup_result,
        backup_datetime_start,
        backup_datetime_finish,
        mixed_aws_result,
        aws_datetime_start,
        aws_datetime_finish,
    )
    analyze_backup_result_mock.assert_called_with(
        mixed_backup_result, infobases, backup_datetime_start, backup_datetime_finish
    )


def test_analyze_results_calls_aws_analyze_if_aws_enabled(
    mocker: MockerFixture, infobases, mixed_backup_result, mixed_aws_result
):
    """
    `analyze_results` calls `analyze_s3_result` if AWS_ENABLED is True
    """
    backup_datetime_start = datetime.now()
    backup_datetime_finish = backup_datetime_start + timedelta(minutes=5)
    aws_datetime_start = datetime.now()
    aws_datetime_finish = aws_datetime_start + timedelta(minutes=5)
    mocker.patch("conf.settings.AWS_ENABLED", new_callable=PropertyMock(return_value=True))
    mocker.patch("backup.analyze_backup_result")
    analyze_s3_result_mock = mocker.patch("backup.analyze_s3_result")
    analyze_results(
        infobases,
        mixed_backup_result,
        backup_datetime_start,
        backup_datetime_finish,
        mixed_aws_result,
        aws_datetime_start,
        aws_datetime_finish,
    )
    analyze_s3_result_mock.assert_called_with(mixed_aws_result, infobases, aws_datetime_start, aws_datetime_finish)


def test_send_email_notification_does_nothing_when_disabled(
    mocker: MockerFixture, mixed_backup_result, mixed_aws_result
):
    """
    `send_email_notification` does nothing when NOTIFY_EMAIL_ENABLED is False
    """
    send_notification_mock = mocker.patch("backup.send_notification")
    send_email_notification(mixed_backup_result, mixed_aws_result)
    send_notification_mock.assert_not_called()


def test_send_email_notification_calls_inner_send_func(mocker: MockerFixture, mixed_backup_result, mixed_aws_result):
    """
    `send_email_notification` calls inner util func for sending notification
    """
    mocker.patch(
        "conf.settings.NOTIFY_EMAIL_ENABLED",
        new_callable=PropertyMock(return_value=True),
    )
    mocker.patch("backup.make_html_table")
    send_notification_mock = mocker.patch("backup.send_notification")
    send_email_notification(mixed_backup_result, mixed_aws_result)
    send_notification_mock.assert_called_once()


def test_send_email_notification_makes_backup_table(mocker: MockerFixture, mixed_backup_result, mixed_aws_result):
    """
    `send_email_notification` calls `make_html_table` for backup results
    """
    mocker.patch(
        "conf.settings.NOTIFY_EMAIL_ENABLED",
        new_callable=PropertyMock(return_value=True),
    )
    mocker.patch("backup.send_notification")
    make_html_table_mock = mocker.patch("backup.make_html_table")
    send_email_notification(mixed_backup_result, mixed_aws_result)
    make_html_table_mock.assert_called_with("Backup", mixed_backup_result)


def test_send_email_notification_not_makes_aws_table_when_aws_disabled(
    mocker: MockerFixture, mixed_backup_result, mixed_aws_result
):
    """
    `send_email_notification` calls `make_html_table` only for backup results when AWS_ENABLED is False
    """
    mocker.patch(
        "conf.settings.NOTIFY_EMAIL_ENABLED",
        new_callable=PropertyMock(return_value=True),
    )
    mocker.patch("backup.send_notification")
    make_html_table_mock = mocker.patch("backup.make_html_table")
    send_email_notification(mixed_backup_result, mixed_aws_result)
    make_html_table_mock.assert_called_once()


def test_send_email_notification_makes_aws_table_when_aws_enabled(
    mocker: MockerFixture, mixed_backup_result, mixed_aws_result
):
    """
    `send_email_notification` calls `make_html_table` both for aws and backup results
    """
    mocker.patch(
        "conf.settings.NOTIFY_EMAIL_ENABLED",
        new_callable=PropertyMock(return_value=True),
    )
    mocker.patch("conf.settings.AWS_ENABLED", new_callable=PropertyMock(return_value=True))
    mocker.patch("backup.send_notification")
    make_html_table_mock = mocker.patch("backup.make_html_table")
    send_email_notification(mixed_backup_result, mixed_aws_result)
    make_html_table_mock.assert_called_with("AWS upload", mixed_aws_result)


def test_send_email_notification_makes_aws_and_backup_tables_when_aws_enabled(
    mocker: MockerFixture, mixed_backup_result, mixed_aws_result
):
    """
    `send_email_notification` calls `make_html_table` both for aws and backup results
    """
    mocker.patch(
        "conf.settings.NOTIFY_EMAIL_ENABLED",
        new_callable=PropertyMock(return_value=True),
    )
    mocker.patch("conf.settings.AWS_ENABLED", new_callable=PropertyMock(return_value=True))
    mocker.patch("backup.send_notification")
    make_html_table_mock = mocker.patch("backup.make_html_table")
    send_email_notification(mixed_backup_result, mixed_aws_result)
    assert make_html_table_mock.call_count == 2


def test_create_aws_upload_task_does_not_create_task_if_aws_not_enabled(mocker: MockerFixture, infobase):
    """
    `create_aws_upload_task` does not create task if `AWS_ENABLED` is False
    """
    semaphore = asyncio.Semaphore(1)
    value = core_models.InfoBaseBackupTaskResult(infobase, True, "test/backup.path")
    mocker.patch("conf.settings.AWS_ENABLED", new_callable=PropertyMock(return_value=False))
    mock_create_task = mocker.patch("asyncio.create_task")
    create_aws_upload_task(value, semaphore)
    mock_create_task.assert_not_called()


def test_create_aws_upload_task_creates_task_if_aws_enabled(mocker: MockerFixture, infobase):
    """
    `create_aws_upload_task` creates task if `AWS_ENABLED` is True
    """
    semaphore = asyncio.Semaphore(1)
    value = core_models.InfoBaseBackupTaskResult(infobase, True, "test/backup.path")
    mocker.patch("conf.settings.AWS_ENABLED", new_callable=PropertyMock(return_value=True))
    mock_create_task = mocker.patch("asyncio.create_task")
    create_aws_upload_task(value, semaphore)
    mock_create_task.assert_called_once()


def test_create_aws_upload_task_creates_proper_task(mocker: MockerFixture, infobase):
    """
    `create_aws_upload_task` creates task with required coro inside
    """
    semaphore = asyncio.Semaphore(1)
    value = core_models.InfoBaseBackupTaskResult(infobase, True, "test/backup.path")
    mocker.patch("conf.settings.AWS_ENABLED", new_callable=PropertyMock(return_value=True))
    mocker.patch("asyncio.create_task")
    mock_upload_infobase_to_s3 = mocker.patch("core.aws.upload_infobase_to_s3")
    create_aws_upload_task(value, semaphore)
    mock_upload_infobase_to_s3.assert_called_once()


def test_create_backup_replication_task_does_not_create_task_if_replication_not_enabled(
    mocker: MockerFixture, infobase
):
    """
    `create_backup_replication_task` does not create task if `BACKUP_REPLICATION` is False
    """
    semaphore = asyncio.Semaphore(1)
    value = core_models.InfoBaseBackupTaskResult(infobase, True, "test/backup.path")
    mocker.patch(
        "conf.settings.BACKUP_REPLICATION",
        new_callable=PropertyMock(return_value=False),
    )
    mock_create_task = mocker.patch("asyncio.create_task")
    create_backup_replication_task(value, semaphore)
    mock_create_task.assert_not_called()


def test_create_backup_replication_task_creates_task_if_replication_enabled(mocker: MockerFixture, infobase):
    """
    `create_backup_replication_task` creates task if `BACKUP_REPLICATION` is True
    """
    semaphore = asyncio.Semaphore(1)
    value = core_models.InfoBaseBackupTaskResult(infobase, True, "test/backup.path")
    mocker.patch("conf.settings.BACKUP_REPLICATION", new_callable=PropertyMock(return_value=True))
    mock_create_task = mocker.patch("asyncio.create_task")
    create_backup_replication_task(value, semaphore)
    mock_create_task.assert_called_once()


def test_create_backup_replication_task_creates_proper_task(mocker: MockerFixture, infobase):
    """
    `create_backup_replication_task` creates task with required coro inside
    """
    semaphore = asyncio.Semaphore(1)
    value = core_models.InfoBaseBackupTaskResult(infobase, True, "test/backup.path")
    mocker.patch("conf.settings.BACKUP_REPLICATION", new_callable=PropertyMock(return_value=True))
    mocker.patch("asyncio.create_task")
    mock_replicate_info_base = mocker.patch("backup.replicate_info_base")
    create_backup_replication_task(value, semaphore)
    mock_replicate_info_base.assert_called_once()
