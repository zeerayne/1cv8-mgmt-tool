import logging

from datetime import datetime, timedelta

from core.analyze import analyze_result


def test_analyze_result_all_succeeded(caplog, infobases, success_base_result):
    """
    Log shoud contain info message with exact number of succeeded jobs when all jobs succeeded
    """
    datetime_start = datetime.now()
    datetime_finish = datetime_start + timedelta(minutes=5)
    with caplog.at_level(logging.INFO):
        analyze_result(
            success_base_result,
            infobases,
            datetime_start,
            datetime_finish,
        )
    assert f'{len(infobases)} succeeded' in caplog.text


def test_analyze_result_all_failed(caplog, infobases, failed_base_result):
    """
    Log shoud contain error message with names of failed infobases when all jobs failed
    """
    datetime_start = datetime.now()
    datetime_finish = datetime_start + timedelta(minutes=5)
    with caplog.at_level(logging.ERROR):
        analyze_result(
            failed_base_result,
            infobases,
            datetime_start,
            datetime_finish,
        )
    assert [f'[{infobase}] FAILED' in caplog.text for infobase in infobases] == [True for i in range(len(infobases))]
