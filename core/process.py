import logging
import subprocess
import threading
import time

import settings

from multiprocessing.pool import ThreadPool
from core.cluster import ClusterControlInterface
from core.exceptions import V8Exception


def execute_v8_command(
        ib_name, v8_command, log_filename, permission_code=None, timeout=None
):
    """
    Блокирует новые сеансы информационной базы, блокирует регламентные задания, выгоняет всех пользователей.
    После этого запускает 1С в командном режиме, согласно переданной команде и дожидается завершения выполнения.
    В конце убирает все установленные ранее блокировки.
    Если в результате выполнения операции в командном режиме результат выполнения отличный от 0, выбрасывает исключение
    :param ib_name: Имя информационной базы, для которой будет выполнен запуск 1С в командном режиме
    :param v8_command: Команда запуска 1С в командном режиме. В тексте команды должен быть указан код доступа и лог-файл
    :param log_filename: Полный путь к файлу, куда 1С пишет результат свооей работы, для дублирования в python.logging
    :param permission_code: Код, для блокировки новых сеансов, если параметр отсутвует, блокировка не будет установлена
    """
    # Теоретически можно пользоваться одним объектом на целый поток т.к. все функции отрабатывают последовательно.
    # Но проблема в том, что через некоторые промежутки времени кластер может закрыть соединение, что приведет к
    # исключению. Накладные расходы на создание новых объектов малы, поэтому этот вариант оптимален
    with ClusterControlInterface() as cci:
        agent_connection = cci.get_agent_connection()
        cluster = cci.get_cluster_with_auth(agent_connection)
        working_process_connection = cci.get_working_process_connection_with_info_base_auth()
        # TODO: нужно добавить оптимизацию - объект, который содержит в себе сразу Info и Short описания
        ib_short = cci.get_info_base_short(agent_connection, cluster, ib_name)
        ib = cci.get_info_base(working_process_connection, ib_name)
        if permission_code:
            # Блокирует фоновые задания и новые сеансы
            cci.lock_info_base(working_process_connection, ib, permission_code)
            logging.debug('[{0}] Locked sucessfully'.format(ib_name))
            # Перед завершением сеансов следует взять паузу,
            # потому что фоновые задания всё ещё могут быть запущены спустя несколько секунд
            # после включения блокировки регламентных заданий
            time.sleep(settings.V8_LOCK_INFO_BASE_PAUSE)
            # Принудительно завершает текущие сеансы
            cci.terminate_info_base_sessions(agent_connection, cluster, ib_short)
            del agent_connection
            del cluster
            del ib_short
            del working_process_connection
        v8_process = subprocess.Popen(v8_command)
        logging.debug('[%s] 1cv8.exe PID is %s' % (ib_name, str(v8_process.pid)))
        try:
            v8_process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            v8_process.terminate()
        logging.info('[%s] Return code is %s' % (ib_name, str(v8_process.returncode)))
        if permission_code:
            # Снова получаем соединение с рабочим процессом, потому что за время работы скрипта оно может закрыться
            working_process_connection = cci.get_working_process_connection_with_info_base_auth()
            # Снимает блокировку фоновых заданий и сеансов
            cci.unlock_info_base(working_process_connection, ib)
            del ib
            del working_process_connection
    with open(log_filename) as log_file:
        read_data = log_file.read()
        # remove a trailing newline
        read_data = read_data.rstrip()
        msg = '[%s] Log message <<< %s >>>' % (ib_name, read_data)
        if v8_process.returncode != 0:
            logging.error(msg)
            raise V8Exception(read_data)
        else:
            logging.info(msg)


def pycom_threadpool_initializer():
    # Чтобы создавать COM-объекты в потоках, отличных от MainThread,
    # необходимо инициализировать win32com для кажодго потока
    import pythoncom
    pythoncom.CoInitialize()
    thread_id = threading.get_ident()
    logging.debug('Thread #%d initialized' % thread_id)


def execute_in_threadpool(func, iterable, threads):
    """

    :param func:
    :param iterable:
    :param threads:
    :return:
    """
    logging.debug('Creating pool with %d threads' % threads)
    pool = ThreadPool(threads, initializer=pycom_threadpool_initializer)
    logging.debug('Pool initialized, mapping workload: %d items' % len(iterable))
    result = pool.map(func, iterable)
    logging.debug('Closing pool')
    pool.close()
    logging.debug('Joining pool')
    pool.join()
    succeeded = 0
    failed = 0
    for e in result:
        if e[1]:
            succeeded += 1
        else:
            failed += 1
            logging.error('[%s] FAILED' % e[0])
    logging.info('%d succeeded; %d failed' % (succeeded, failed))
    return [(e[0], e[1]) for e in result if e[1]]
