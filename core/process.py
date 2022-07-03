import asyncio
import logging
from typing import Type

from conf import settings
from core import cluster, utils
from core.exceptions import SubprocessException, V8Exception


log = logging.getLogger(__name__)


def _check_subprocess_return_code(
    ib_name: str,
    subprocess: asyncio.subprocess.Process,
    log_filename: str,
    log_encoding: str,
    exception_class: Type[SubprocessException] = SubprocessException,
    log_output_on_success=False
):
    log.info(f'<{ib_name}> Return code is {str(subprocess.returncode)}')
    log_file_content = utils.read_file_content(log_filename, log_encoding)
    msg = f'<{ib_name}> Log message :: {log_file_content}'
    if subprocess.returncode != 0:
        log.error(msg)
        raise exception_class(log_file_content)
    elif log_output_on_success:
        log.info(msg)


async def execute_v8_command(
    ib_name: str,
    v8_command: str,
    log_filename: str,
    permission_code: str = None,
    timeout: int = None,
    log_output_on_success=False
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
    """
    # Теоретически можно пользоваться одним объектом на целый поток т.к. все функции отрабатывают последовательно.
    # Но проблема в том, что через некоторые промежутки времени кластер может закрыть соединение, что приведет к
    # исключению. Накладные расходы на создание новых объектов малы, поэтому этот вариант оптимален
    with cluster.ClusterControlInterface() as cci:
        if permission_code:
            agent_connection = cci.get_agent_connection()
            cluster_with_auth = cci.get_cluster_with_auth(agent_connection)
            working_process_connection = cci.get_working_process_connection_with_info_base_auth()
            ib = cci.get_info_base(working_process_connection, ib_name)
            # Блокирует фоновые задания и новые сеансы
            cci.lock_info_base(working_process_connection, ib, permission_code)
            # Перед завершением сеансов следует взять паузу,
            # потому что фоновые задания всё ещё могут быть запущены спустя несколько секунд
            # после включения блокировки регламентных заданий
            pause = settings.V8_LOCK_INFO_BASE_PAUSE
            log.debug(f'<{ib_name}> Wait for {pause} seconds')
            await asyncio.sleep(pause)
            ib_short = cci.get_info_base_short(agent_connection, cluster_with_auth, ib_name)
            # Принудительно завершает текущие сеансы
            cci.terminate_info_base_sessions(agent_connection, cluster_with_auth, ib_short)
            del agent_connection
            del cluster_with_auth
            del ib_short
            del working_process_connection
        v8_process = await asyncio.create_subprocess_shell(v8_command)
        log.debug(f'<{ib_name}> 1cv8.exe PID is {str(v8_process.pid)}')
        try:
            await asyncio.wait_for(v8_process.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            await v8_process.terminate()

        if permission_code:
            # Снова получает соединение с рабочим процессом,
            # потому что за время работы процесса 1cv8 оно может закрыться
            working_process_connection = cci.get_working_process_connection_with_info_base_auth()
            # Снимает блокировку фоновых заданий и сеансов
            cci.unlock_info_base(working_process_connection, ib)
            del ib
            del working_process_connection
    _check_subprocess_return_code(ib_name, v8_process, log_filename, 'utf-8-sig', V8Exception, log_output_on_success)


async def execute_subprocess_command(
    ib_name: str, subprocess_command: str, log_filename: str, timeout: int = None, log_output_on_success=False
):
    subprocess = await asyncio.create_subprocess_shell(subprocess_command)
    log.debug(f'<{ib_name}> Subprocess PID is {str(subprocess.pid)}')
    try:
        await asyncio.wait_for(subprocess.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        await subprocess.terminate()
    _check_subprocess_return_code(
        ib_name, subprocess, log_filename, 'utf-8', SubprocessException, log_output_on_success
    )
