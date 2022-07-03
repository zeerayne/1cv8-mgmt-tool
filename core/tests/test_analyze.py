import logging
from datetime import datetime, timedelta

from core.analyze import (
    analyze_backup_result, analyze_maintenance_result, analyze_result, analyze_s3_result, analyze_update_result
)


def test_analyze_result_empty(caplog):
    """
    Analyze shoud notify with log message if no work was done
    """
    datetime_start = datetime.now()
    datetime_finish = datetime_start + timedelta(minutes=5)
    with caplog.at_level(logging.INFO):
        analyze_result([], [], datetime_start, datetime_finish)
    assert 'Nothing was done' in caplog.text


def test_analyze_result_log_subprefix(caplog, infobases, success_base_result):
    """
    Analyze log message shoud contain subrefix, if given
    """
    log_subprefix = 'Test_Subprefix'

    datetime_start = datetime.now()
    datetime_finish = datetime_start + timedelta(minutes=5)
    with caplog.at_level(logging.INFO):
        analyze_result(success_base_result, infobases, datetime_start, datetime_finish, log_subprefix)
    assert log_subprefix in caplog.text


def test_analyze_result_all_succeeded(caplog, infobases, success_base_result):
    """
    Analyze log message shoud contain info message with exact number of succeeded jobs when all jobs succeeded
    """
    datetime_start = datetime.now()
    datetime_finish = datetime_start + timedelta(minutes=5)
    with caplog.at_level(logging.INFO):
        analyze_result(success_base_result, infobases, datetime_start, datetime_finish)
    assert f'{len(infobases)} succeeded' in caplog.text


def test_analyze_result_all_failed(caplog, infobases, failed_base_result):
    """
    Analyze log message shoud contain error message with names of failed infobases when all jobs failed
    """
    datetime_start = datetime.now()
    datetime_finish = datetime_start + timedelta(minutes=5)
    with caplog.at_level(logging.ERROR):
        analyze_result(failed_base_result, infobases, datetime_start, datetime_finish)
    assert [f'[{infobase}] FAILED' in caplog.text for infobase in infobases] == [True for i in range(len(infobases))]


def test_analyze_result_some_missed(caplog, infobases, mixed_base_result):
    """
    Analyze log message shoud contain warning message with names of missed infobases
    when some jobs not provideded any result
    """
    datetime_start = datetime.now()
    datetime_finish = datetime_start + timedelta(minutes=5)
    with caplog.at_level(logging.WARNING):
        analyze_result(mixed_base_result[:-1], infobases, datetime_start, datetime_finish)
    assert f'[{mixed_base_result[-1].infobase_name}] MISSED' in caplog.text


def test_analyze_result_backup(mock_analyze_result, infobases, success_backup_result):
    """
    Analyze backup log should have `Backup` log prefix
    """
    datetime_start = datetime.now()
    datetime_finish = datetime_start + timedelta(minutes=5)
    analyze_backup_result(success_backup_result, infobases, datetime_start, datetime_finish)
    mock_analyze_result.assert_called_with(success_backup_result, infobases, datetime_start, datetime_finish, 'Backup')


def test_analyze_result_maintenance(mock_analyze_result, infobases, success_maintenance_result):
    """
    Analyze maintenance log should have `Maintenance` log prefix
    """
    datetime_start = datetime.now()
    datetime_finish = datetime_start + timedelta(minutes=5)
    analyze_maintenance_result(success_maintenance_result, infobases, datetime_start, datetime_finish)
    mock_analyze_result.assert_called_with(
        success_maintenance_result, infobases, datetime_start, datetime_finish, 'Maintenance'
    )


def test_analyze_result_update(mock_analyze_result, infobases, success_update_result):
    """
    Analyze update log should have `Update` log prefix
    """
    datetime_start = datetime.now()
    datetime_finish = datetime_start + timedelta(minutes=5)
    analyze_update_result(success_update_result, infobases, datetime_start, datetime_finish)
    mock_analyze_result.assert_called_with(success_update_result, infobases, datetime_start, datetime_finish, 'Update')


def test_analyze_result_aws_upload(caplog, infobases, success_aws_result):
    """
    Analyze aws upload log message should have custom `Uploaded` phrase
    """
    datetime_start = datetime.now()
    datetime_finish = datetime_start + timedelta(minutes=5)
    with caplog.at_level(logging.INFO):
        analyze_s3_result(success_aws_result, infobases, datetime_start, datetime_finish)
    assert 'Uploaded' in caplog.text
