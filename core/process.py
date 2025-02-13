import asyncio
import logging
from typing import Type

from conf import settings
from core import utils
from core.cluster import utils as cluster_utils
from core.exceptions import SubprocessException, V8Exception

log = logging.getLogger(__name__)


def _check_subprocess_return_code(
    ib_name: str,
    subprocess: asyncio.subprocess.Process,
    log_filename: str,
    log_encoding: str,
    exception_class: Type[SubprocessException] = SubprocessException,
    log_output_on_success: bool = False,
):
    log.info(f"<{ib_name}> Return code is {subprocess.returncode}")
    log_file_content = utils.read_file_content(log_filename, log_encoding)
    msg = f"<{ib_name}> Log message :: {log_file_content}"
    if subprocess.returncode != 0:
        log.error(msg)
        raise exception_class(log_file_content)
    elif log_output_on_success:
        log.info(msg)


async def _kill_process_emergency(pid: int):
    try:
        log.info(f"Try to kill PID {pid} with taskkill")
        taskkill_process = await asyncio.create_subprocess_shell(f"taskkill /PID {pid} /F")
        await asyncio.wait_for(taskkill_process.communicate(), timeout=5)
        if taskkill_process.returncode != 0:
            log.error(f"Process with PID {pid} was not killed with taskkill")
        else:
            log.info(f"Process with PID {pid} successfully killed with taskkill")
    except Exception as e:
        log.exception(f"Error while calling taskkill: {e}")


async def _wait_for_subprocess(subprocess: asyncio.subprocess.Process, timeout: int = None):
    pid = subprocess.pid
    try:
        await asyncio.wait_for(subprocess.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        try:
            coro = subprocess.terminate()
            if coro:
                await coro
        except Exception as e:
            log.exception(f"Process with PID {pid} can not be terminated: {e}")
            await _kill_process_emergency(pid)
    except Exception as e:
        log.exception(f"Exception while communicating with subprocess: {e}")
        await _kill_process_emergency(pid)


async def execute_v8_command(
    ib_name: str,
    v8_command: str,
    log_filename: str,
    permission_code: str = None,
    timeout: int = None,
    log_output_on_success: bool = False,
    create_subprocess_pause: float = 0.0,
):
    """
    Блокирует новые сеансы информационной базы, блокирует регламентные задания, выгоняет всех пользователей.
    После этого запускает 1С в командном режиме, согласно переданной команде и дожидается завершения выполнения.
    В конце убирает все установленные ранее блокировки.
    Если в результате выполнения операции в командном режиме результат выполнения отличный от 0, выбрасывает исключение
    :param ib_name: Имя информационной базы, для которой будет выполнен запуск 1С в командном режиме
    :param v8_command: Команда запуска 1С в командном режиме. В тексте команды должен быть указан код доступа и лог-файл
    :param log_filename: Полный путь к файлу, куда 1С пишет результат свооей работы, для дублирования в python.log
    :param permission_code: Код, для блокировки новых сеансов, если параметр отсутвует, блокировка не будет установлена
    :param timeout: Максимальное время работы внешнего процесса, по истечению которого он будет принудительно завершен
    :param log_output_on_success: Выводить в консоль лог внешнего процесса в случае его успешного завершения
    :param create_subprocess_pause: Пауза перед запуском внешнего процесса
    """
    # Теоретически можно пользоваться одним объектом на целый поток т.к. все функции отрабатывают последовательно.
    # Но проблема в том, что через некоторые промежутки времени кластер может закрыть соединение, что приведет к
    # исключению. Накладные расходы на создание новых объектов малы, поэтому этот вариант оптимален
    cci = cluster_utils.get_cluster_controller()
    if permission_code:
        # Блокирует фоновые задания и новые сеансы
        cci.lock_info_base(ib_name, permission_code)
        # Перед завершением сеансов следует взять паузу,
        # потому что фоновые задания всё ещё могут быть запущены спустя несколько секунд
        # после включения блокировки регламентных заданий
        pause = settings.V8_LOCK_INFO_BASE_PAUSE
        log.debug(f"<{ib_name}> Infobase locked. Wait for {pause} seconds")
        await asyncio.sleep(pause)
    # Принудительно завершает текущие сеансы
    cci.terminate_info_base_sessions(ib_name)
    if create_subprocess_pause:
        log.debug(f"<{ib_name}> Pause before creating process. Wait for {create_subprocess_pause:.2f} seconds")
        await asyncio.sleep(create_subprocess_pause)
    v8_process = await asyncio.create_subprocess_shell(v8_command)
    log.debug(f"<{ib_name}> 1cv8 PID is {v8_process.pid}")
    await _wait_for_subprocess(v8_process, timeout)
    if permission_code:
        # Снимает блокировку фоновых заданий и сеансов
        cci.unlock_info_base(ib_name)
    _check_subprocess_return_code(
        ib_name,
        v8_process,
        log_filename,
        "utf-8-sig",
        V8Exception,
        log_output_on_success,
    )


async def execute_subprocess_command(
    ib_name: str,
    subprocess_command: str,
    log_filename: str,
    env: dict = None,
    timeout: int = None,
    log_output_on_success: bool = False,
):
    subprc_coro = (
        asyncio.create_subprocess_shell(subprocess_command, env=env)
        if env is not None
        else asyncio.create_subprocess_shell(subprocess_command)
    )
    subprocess = await subprc_coro
    log.debug(f"<{ib_name}> Subprocess PID is {subprocess.pid}")
    await _wait_for_subprocess(subprocess, timeout)
    _check_subprocess_return_code(
        ib_name,
        subprocess,
        log_filename,
        "utf-8",
        SubprocessException,
        log_output_on_success,
    )
