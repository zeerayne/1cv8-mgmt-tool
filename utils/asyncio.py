import asyncio
import logging
import sys
from typing import Awaitable

log = logging.getLogger(__name__)


def initialize_event_loop(payload_coroutine: Awaitable):
    if sys.version_info < (3, 10):
        # Использование asyncio.run() в windows бросает исключение
        # `RuntimeError: Event loop is closed` при завершении run.
        # WindowsSelectorEventLoopPolicy не работает с подпроцессами полноценно в python 3.8
        asyncio.get_event_loop().run_until_complete(payload_coroutine)
    else:
        asyncio.run(payload_coroutine)


def initialize_semaphore(concurrency: int, log_prefix: str, log_suffix: str = None) -> asyncio.Semaphore:
    semaphore = asyncio.Semaphore(concurrency)
    log_mixin = f" {log_suffix}" if log_suffix else ""
    log.info(f"<{log_prefix}> Asyncio semaphore initialized: {concurrency}{log_mixin} concurrency")
    return semaphore
