import ntpath
import datetime
import logging
import os

import pywintypes
import settings

from typing import Union

from core import version
from core.cluster import ClusterControlInterface
from core.exceptions import V8Exception

platformPath = settings.V8_PLATFORM_PATH
platformVersion = version.find_platform_last_version(platformPath)


log = logging.getLogger(__name__)


def get_platform_full_path() -> str:
    full_path = os.path.join(platformPath, platformVersion, 'bin', '1cv8.exe')
    return full_path


def get_server_address() -> str:
    address = settings.V8_SERVER_AGENT['address']
    return address


def get_formatted_current_datetime() -> str:
    time_str = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    return time_str


def get_formatted_date(datetime_value: Union[datetime.datetime, datetime.date]) -> str:
    time_str = datetime_value.strftime("%Y-%m-%d")
    return time_str


def get_ib_and_time_string(ib_name: str) -> str:
    time_str = get_formatted_current_datetime()
    ib_and_time_str = f'{ib_name}_{time_str}'
    return ib_and_time_str


def append_file_extension_to_string(string: str, file_ext: str) -> str:
    string_with_extension = f'{string}.{file_ext}'
    return string_with_extension


def get_ib_and_time_filename(ib_name: str, file_ext: str) -> str:
    ib_and_time_str = get_ib_and_time_string(ib_name)
    ib_and_time_filename = append_file_extension_to_string(ib_and_time_str, file_ext)
    return ib_and_time_filename


def get_info_bases():
    """
    Получает именя всех ИБ, кроме указанных в списке INFO_BASES_EXCLUDE
    :return: массив с именами ИБ
    """
    with ClusterControlInterface() as cci:
        working_process_connection = cci.get_working_process_connection_with_info_base_auth()

        info_bases = cci.get_info_bases(working_process_connection)
        info_bases = [
            ib.Name for ib in info_bases if ib.Name.lower() not in [ib.lower() for ib in settings.V8_INFO_BASES_EXCLUDE]
        ]
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
        log.exception(f'[{ib_name}] COM Error occured')
        # Если произошла ошибка, пытаемся снять блокировку ИБ
        try:
            with ClusterControlInterface() as cci:
                working_process_connection = cci.get_working_process_connection_with_info_base_auth()
                ib = cci.get_info_base(working_process_connection, ib_name)
                cci.unlock_info_base(working_process_connection, ib)
                del working_process_connection
        except pywintypes.com_error as e:
            log.exception(f'[{ib_name}] COM Error occured during handling another COM Error')
        # После разблокировки возвращаем неуспешный результат
        return ib_name, False
    except V8Exception as e:
        return ib_name, False
    return ib_name, result
