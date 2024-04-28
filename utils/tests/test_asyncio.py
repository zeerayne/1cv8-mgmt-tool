import asyncio
import sys
from unittest.mock import AsyncMock

from pytest_mock import MockerFixture

from utils.asyncio import initialize_event_loop, initialize_semaphore


def test_initialize_event_loop(mocker: MockerFixture):
    """
    Event loop is initialized successfully
    """
    payload = AsyncMock()
    if sys.version_info < (3, 10):
        mock_asyncio = mocker.patch("asyncio.get_event_loop")
        initialize_event_loop(payload)
        mock_asyncio.return_value.run_until_complete.assert_called_once_with(payload)
    else:
        mock_asyncio = mocker.patch("asyncio.run")
        initialize_event_loop(payload)
        mock_asyncio.assert_called_once_with(payload)


def test_initialize_semaphore_returns_semaphore(mocker: MockerFixture):
    """
    `initialize_semaphore` returns semaphore
    """
    concurrency = 1
    log_prefix = "test_prefix"
    mocker.patch("asyncio.run")
    result = initialize_semaphore(concurrency, log_prefix)
    assert isinstance(result, asyncio.Semaphore)


def test_initialize_creates_semaphore_with_required_concurrency(mocker: MockerFixture):
    """
    `initialize_semaphore` creates semaphore with required concurrency
    """
    concurrency = 1
    log_prefix = "test_prefix"
    mock_semaphore = mocker.patch("asyncio.Semaphore")
    initialize_semaphore(concurrency, log_prefix)
    mock_semaphore.assert_called_with(concurrency)
