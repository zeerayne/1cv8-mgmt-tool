import glob
import logging
import ntpath
import os
import platform
from datetime import date, datetime, timedelta
from typing import Tuple, Union

import aiofiles.os

from conf import settings
from core import version
from core.cluster import utils as cluster_utils

log = logging.getLogger(__name__)


def get_platform_full_path() -> str:
    platformPath = settings.V8_PLATFORM_PATH
    platformVersion = version.find_platform_last_version(platformPath)
    platformDirectory = os.path.join(platformPath, str(platformVersion))
    if platform.system() == "Windows":
        full_path = os.path.join(platformDirectory, "bin", "1cv8.exe")
    if platform.system() == "Linux":
        full_path = os.path.join(platformDirectory, "1cv8")
    return full_path


def get_formatted_current_datetime() -> str:
    return datetime.now().strftime(settings.DATETIME_FORMAT)


def get_formatted_date_for_1cv8(datetime_value: Union[datetime, date]) -> str:
    return datetime_value.strftime(settings.DATE_FORMAT_1CV8)


def get_ib_name_with_separator(ib_name: str):
    return f"{ib_name}{settings.FILENAME_SEPARATOR}"


def get_infobase_glob_pattern(ib_name: str, file_extension: str = "*"):
    return f"*{get_ib_name_with_separator(ib_name)}*.{file_extension}"


def get_ib_and_time_string(ib_name: str) -> str:
    return f"{get_ib_name_with_separator(ib_name)}{get_formatted_current_datetime()}"


def append_file_extension_to_string(string: str, file_ext: str) -> str:
    return f"{string}.{file_ext}"


def get_ib_and_time_filename(ib_name: str, file_ext: str) -> str:
    ib_and_time_str = get_ib_and_time_string(ib_name)
    ib_and_time_filename = append_file_extension_to_string(ib_and_time_str, file_ext)
    return ib_and_time_filename


def get_info_bases():
    cci = cluster_utils.get_cluster_controller()
    info_bases = cci.get_info_bases()
    return info_bases


def get_info_base_credentials(ib_name) -> Tuple[str, str]:
    """
    Получает имя пользователя и пароль для инфомационной базы. Поиск производится в настройках.
    Если пара логин/пароль не найдена, возвращает пару по умолчанию
    :param ib_name: имя ИБ
    :return: tuple(login, pwd)
    """
    try:
        creds = settings.V8_INFOBASES_CREDENTIALS[ib_name]
    except KeyError:
        creds = settings.V8_INFOBASES_CREDENTIALS["default"]
    return creds


def path_leaf(path: str) -> str:
    """
    Из полного пути к файлу получает только имя файла
    :param path: Полный путь к файлу
    :return: Имя файла
    """
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)


def read_file_content(filename, file_encoding="utf-8"):
    with open(filename, "r", encoding=file_encoding) as file:
        read_data = file.read()
        # remove a trailing newline
        read_data = read_data.rstrip()
    return read_data


async def remove_old_files_by_pattern(pattern: str, retention_days: int):
    """
    Удаляет файлы, дата изменения которых более чем <retention_days> назад
    :param pattern: паттерн пути и имени файлов для модуля glob https://docs.python.org/3/library/glob.html
    :param retention_days: определяет, насколько старые файлы будут удалены
    """
    files = glob.glob(pathname=pattern, recursive=False)
    ts = (datetime.now() - timedelta(days=retention_days)).timestamp()
    files_to_remove = [b for b in files if ts - os.path.getmtime(b) > 0]
    for f in files_to_remove:
        await aiofiles.os.remove(f)
