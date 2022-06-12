import ntpath
import datetime
import logging
import os

try:
    import pywintypes
except ImportError:
    from surrogate import surrogate
    surrogate('pywintypes').prepare()
    import pywintypes
    pywintypes.com_error = Exception

from typing import Union, List, Tuple

from conf import settings
from core import version
from core.cluster import ClusterControlInterface
from core.exceptions import V8Exception
import core.types as core_types


log = logging.getLogger(__name__)


def get_platform_full_path() -> str:
    platformPath = settings.V8_PLATFORM_PATH
    platformVersion = version.find_platform_last_version(platformPath)
    full_path = os.path.join(platformPath, str(platformVersion), 'bin', '1cv8.exe')
    return full_path


def get_formatted_current_datetime() -> str:
    return datetime.datetime.now().strftime(settings.DATETIME_FORMAT)


def get_formatted_date(datetime_value: Union[datetime.datetime, datetime.date]) -> str:
    return datetime_value.strftime(settings.DATE_FORMAT)


def get_ib_name_with_separator(ib_name: str):
    return f'{ib_name}{settings.FILENAME_SEPARATOR}'


def get_ib_and_time_string(ib_name: str) -> str:
    return f'{get_ib_name_with_separator(ib_name)}{get_formatted_current_datetime()}'


def append_file_extension_to_string(string: str, file_ext: str) -> str:
    return f'{string}.{file_ext}'


def get_ib_and_time_filename(ib_name: str, file_ext: str) -> str:
    ib_and_time_str = get_ib_and_time_string(ib_name)
    ib_and_time_filename = append_file_extension_to_string(ib_and_time_str, file_ext)
    return ib_and_time_filename


def get_info_bases() -> List[str]:
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


def get_info_base_credentials(ib_name) -> Tuple[str, str]:
    """
    Получает имя пользователя и пароль для инфомационной базы. Поиск производится в настройках.
    Если пара логин/пароль не найдена, возвращает пару по умолчанию
    :param ib_name: имя ИБ
    :return: tuple(login, pwd)
    """
    try:
        creds = settings.V8_INFO_BASES_CREDENTIALS[ib_name]
    except KeyError:
        creds = settings.V8_INFO_BASES_CREDENTIALS['default']
    return creds


def path_leaf(path: str) -> str:
    """
    Из полного пути к файлу получает только имя файла
    :param path: Полный путь к файлу
    :return: Имя файла
    """
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)


async def com_func_wrapper(func, ib_name: str, **kwargs) -> core_types.InfoBaseTaskResultBase:
    """
    Оборачивает функцию для обработки COM-ошибок
    :param func: функция, которая будет обёрнута
    :param ib_name: имя информационной базы
    :return: Массив ib_name, func_result
    """
    try:
        result = await func(ib_name, **kwargs)
    except pywintypes.com_error as e:
        log.exception(f'<{ib_name}> COM Error occured')
        # Если произошла ошибка, пытаемся снять блокировку ИБ
        try:
            with ClusterControlInterface() as cci:
                working_process_connection = cci.get_working_process_connection_with_info_base_auth()
                ib = cci.get_info_base(working_process_connection, ib_name)
                cci.unlock_info_base(working_process_connection, ib)
                del working_process_connection
        except pywintypes.com_error as e:
            log.exception(f'<{ib_name}> COM Error occured during handling another COM Error')
        # После разблокировки возвращаем неуспешный результат
        return core_types.InfoBaseTaskResultBase(ib_name, False)
    except V8Exception as e:
        return core_types.InfoBaseTaskResultBase(ib_name, False)
    return result


def read_file_content(filename, file_encoding='utf-8'):
    with open(filename, 'r', encoding=file_encoding) as file:
        read_data = file.read()
        # remove a trailing newline
        read_data = read_data.rstrip()
    return read_data
