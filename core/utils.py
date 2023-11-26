import glob
import logging
import ntpath
import os
import platform
from datetime import date, datetime, timedelta
from typing import List, Tuple, Union

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


def append_permission_code_to_v8_command(v8_command: str, permission_code: str) -> str:
    if permission_code:
        return v8_command + rf'/UC "{permission_code}" '
    else:
        return v8_command


def get_infobase_connection_string_for_v8_command(ib_name: str) -> str:
    if infobase_is_in_cluster(ib_name):
        return rf"/S {cluster_utils.get_server_agent_address()}\{ib_name}"
    else:
        return rf"/F {settings.V8_FILE_INFOBASES[ib_name]}"


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


def get_info_bases() -> List[str]:
    info_bases = []
    if settings.V8_CLUSTER_ENABLED:
        cci = cluster_utils.get_cluster_controller()
        info_bases += cci.get_info_bases()
    if settings.V8_FILE_ENABLED:
        info_bases += settings.V8_FILE_INFOBASES.keys()
    return info_bases


def infobase_is_in_file(ib_name: str) -> bool:
    return ib_name in settings.V8_FILE_INFOBASES


def infobase_is_in_cluster(ib_name: str) -> bool:
    return not infobase_is_in_file(ib_name)


def get_info_base_credentials(ib_name: str) -> Tuple[str, str]:
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


def get_v8_command_commons(
    ib_name: str,
    log_filename: str,
    log_truncate: bool = False,
    mode: str = "DESIGNER",
    permission_code: str = None,
    disable_diaglos: bool = False,
) -> str:
    info_base_user, info_base_pwd = get_info_base_credentials(ib_name)
    v8_command_commons = (
        rf'"{get_platform_full_path()}" '
        rf"{mode} {get_infobase_connection_string_for_v8_command(ib_name)} "
        rf'/N"{info_base_user}" /P"{info_base_pwd}" '
        rf"/Out {log_filename}{'' if log_truncate else ' -NoTruncate'} "
        rf"{'/DisableStartupDialogs /DisableStartupMessages ' if disable_diaglos else ''}"
    )
    v8_command_commons = append_permission_code_to_v8_command(v8_command_commons, permission_code)
    return v8_command_commons


def assemble_backup_v8_command(ib_name: str, permission_code: str, log_filename: str, dt_filename: str) -> str:
    """
    Формирует команду для выгрузки
    """
    # https://its.1c.ru/db/v838doc#bookmark:adm:TI000000526
    commons = get_v8_command_commons(ib_name, log_filename, permission_code=permission_code)
    v8_command = rf"{commons} /DumpIB {dt_filename} "
    log.debug(f"<{ib_name}> Created dump command [{v8_command}]")
    return v8_command


def assemble_update_v8_command(ib_name: str, permission_code: str, update_filename: str, log_filename: str) -> str:
    """
    Формирует команду для обновления ИБ
    """
    # https://its.1c.ru/db/v838doc#bookmark:adm:TI000000530
    commons = get_v8_command_commons(ib_name, log_filename, permission_code=permission_code, disable_diaglos=True)
    v8_command = rf'{commons} /UpdateCfg "{update_filename}" -force /UpdateDBCfg -Dynamic- -Server '
    v8_command = append_permission_code_to_v8_command(v8_command, permission_code)
    log.debug(f"<{ib_name}> Created update command [{v8_command}]")
    return v8_command


def assemble_maintenance_v8_command(ib_name: str, reduce_date: str, log_filename: str) -> str:
    """
    Формирует команду для усечения журнала регистрации
    """
    # https://its.1c.ru/db/v838doc#bookmark:adm:TI000000526
    commons = get_v8_command_commons(ib_name, log_filename)
    v8_command = rf"{commons} /ReduceEventLogSize {reduce_date} "
    log.debug(f"<{ib_name}> Created maintenance command [{v8_command}]")
    return v8_command


def assemble_lock_v8_command(ib_name: str, permission_code: str, log_filename: str) -> str:
    """
    Формирует команду для запрещения начала сеансов
    """
    commons = get_v8_command_commons(
        ib_name,
        log_filename,
        log_truncate=True,
        mode="ENTERPRISE",
        permission_code=permission_code,
        disable_diaglos=True,
    )
    v8_command = rf"{commons} /C ЗавершитьРаботуПользователей "
    log.debug(f"<{ib_name}> Created lock command [{v8_command}]")
    return v8_command


def assemble_unlock_v8_command(ib_name: str, permission_code: str, log_filename: str) -> str:
    """
    Формирует команду для снятия блокировки начала сеансов
    """
    commons = get_v8_command_commons(
        ib_name,
        log_filename,
        log_truncate=True,
        mode="ENTERPRISE",
        permission_code=permission_code,
        disable_diaglos=True,
    )
    v8_command = rf"{commons} /C РазрешитьРаботуПользователей "
    log.debug(f"<{ib_name}> Created unlock command [{v8_command}]")
    return v8_command
