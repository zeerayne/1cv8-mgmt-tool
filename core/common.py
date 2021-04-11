import logging
import ntpath
import pywintypes
import settings
import time
from core import version
from core.cluster import ClusterControlInterface
from core.exceptions import V8Exception
from util.debug import is_debug
from util.debug import DEBUG_MONKEY_PATCH

platformPath = settings.V8_PLATFORM_PATH
platformVersion = version.find_platform_last_version(platformPath)


def get_platform_full_path():
    full_path = platformPath + platformVersion + '\\bin\\1cv8.exe'
    return full_path


def get_server_address():
    address = settings.V8_SERVER_AGENT['address']
    return address


def get_formatted_current_datetime():
    time_str = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime(time.time()))
    return time_str


def get_formatted_date(datetime_value):
    time_str = time.strftime("%Y-%m-%d", datetime_value.timetuple())
    return time_str


def get_info_bases():
    """
    Получает именя всех ИБ, кроме указанных в списке INFO_BASES_EXCLUDE
    :return: массив с именами ИБ
    """
    if is_debug():
        with open(DEBUG_MONKEY_PATCH, 'r', encoding='utf-8') as debug_file:
            for line in debug_file:
                if 'info_bases' in line:
                    _locals = {}
                    exec(line, globals(), _locals)
                    return _locals['info_bases']
    with ClusterControlInterface() as cci:
        working_process_connection = cci.get_working_process_connection_with_info_base_auth()

        info_bases = cci.get_info_bases(working_process_connection)
        info_bases = [ib.Name for ib in info_bases if ib.Name.lower() not in
                    [ib.lower() for ib in settings.V8_INFO_BASES_EXCLUDE]]
        del working_process_connection
        return info_bases


def get_info_base_credentials(ib_name):
    """
    Получает имя пользователя и пароль для инфомационной базы. Поиск производится в настройках.
    Если пара логин/пароль не найдена, возвращает пару по умолчанию
    :param ib_name: имя ИБ
    :return: tuple(login, pwd)
    """
    try:
        creds = settings.V8_INFO_BASE_CREDENTIALS[ib_name]
    except KeyError:
        creds = settings.V8_INFO_BASE_CREDENTIALS[settings.DEFAULT_DICT_KEY]
    return creds


def path_leaf(path):
    """
    Из полного пути к файлу получает только имя файла
    :param path: Полный путь к файлу
    :return: Имя файла
    """
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)


def com_func_wrapper(func, ib_name, **kwargs):
    """
    Оборачивает функцию для обработки COM-ошибок
    :param func: функция, которая будет обёрнута
    :param ib_name: имя информационной базы
    :return: Массив ib_name, func_result
    """
    try:
        result = func(ib_name, **kwargs)
    except pywintypes.com_error as e:
        logging.exception('[%s] COM Error occured' % ib_name)
        # Если произошла ошибка, пытаемся снять блокировку ИБ
        try:
            with ClusterControlInterface() as cci:
                working_process_connection = cci.get_working_process_connection_with_info_base_auth()
                ib = cci.get_info_base(working_process_connection, ib_name)
                cci.unlock_info_base(working_process_connection, ib)
                del working_process_connection
        except pywintypes.com_error as e:
            logging.exception('[%s] COM Error occured during handling another COM Error' % ib_name)
        # После разблокировки возвращаем неуспешный результат
        return ib_name, False
    except V8Exception as e:
        return ib_name, False
    return ib_name, result
