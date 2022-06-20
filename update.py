import asyncio
import os.path
import re
import sys
import glob
import itertools
import logging
import pywintypes
import random

from datetime import datetime
from packaging.version import Version
from typing import List, Tuple

import core.types as core_types

from conf import settings
from core import cluster, utils
from core.analyze import analyze_update_result
from core.process import execute_v8_command
from core.version import get_version_from_string


log = logging.getLogger(__name__)
log_prefix = 'Update'


def _find_suitable_manifests(manifests: List[str], name_in_metadata: str, version_in_metadata: Version) -> List[Tuple[str, Version]]:
    """
    Получает все манифесты обновлений для конфигурации из списка манифестов.
    Поиск производится по имени конфигурации и по её версии.
    Будут возвращены только те манифесты обновлений, которые могут быть применены к текущей конфигурации
    :param manifests: Список файлов манифестов
    :param name_in_metadata: Имя конфигурации из её метаданных
    :param version_in_metadata: LooseVersion версии конфигурации из её метаданных
    :return: Массив с кортежами вида (manifest_file_path, version_in_manifest)
    """
    suitable_manifests = []
    for m in manifests:
        with open(file=m, mode='r', encoding='UTF-8') as manifest_file:
            manifest_text = manifest_file.read()
            name_matches = re.findall("Name=(.*)", manifest_text)
            name_in_manifest = name_matches[0]
            version_matches = re.findall("Version=(.*)", manifest_text)
            version_in_manifest = get_version_from_string(version_matches[0])
        # Наименование конфигурации должно совпадать, а версия обновления должна быть больше, чем версия ИБ
        # Если это так, необходимо проверить, можно ли обновить текущую версию до новой
        if name_in_manifest == name_in_metadata and version_in_manifest > version_in_metadata:
            with open(file=m.replace('1cv8.mft', 'UpdInfo.txt'), mode='r', encoding='UTF-8') as updinfo_file:
                updinfo_text = updinfo_file.read()
                from_versions_matches = re.findall("FromVersions=(.*)", updinfo_text)
                from_version_match_result = from_versions_matches[0]
            if from_version_match_result.startswith(';'):
                from_version_match_result = from_version_match_result[1:]
            if from_version_match_result.endswith(';'):
                from_version_match_result = from_version_match_result[:-1]
            from_versions_array = from_version_match_result.split(";")
            # Если обновление применимо к текущей версии ИБ, добавляем его в список доступных
            if version_in_metadata in from_versions_array:
                suitable_manifests.append((m, version_in_manifest))
    return suitable_manifests


def _get_suitable_manifest(manifests: List[str], name_in_metadata: str, version_in_metadata: Version) -> Tuple[str, Version]:
    """
    Получает наиболее подходящий манифест обновления для текущей конфигурации
    :param manifests: Список файлов манифестов
    :param name_in_metadata: Имя конфигурации из её метаданных
    :param version_in_metadata: LooseVersion версии конфигурации из её метаданных
    :return: Кортеж (manifest_file_path, version_in_manifest)
    """
    suitable_manifests = _find_suitable_manifests(manifests, name_in_metadata, version_in_metadata)
    # После того, как найдены подходящие обновления, нужно выбрать самое свежее из них
    # TODO: необходимо предусмотреть возможность выбирать, к примеру сначала самое старое, и обновляться поэтапно
    if suitable_manifests:
        selected_manifest = max(suitable_manifests, key=lambda item: item[1])
        return selected_manifest
    else:
        return None


def _get_update_chain(manifests: List[str], name_in_metadata: str, version_in_metadata: Version) -> Tuple[List[Tuple[str, Version]], bool]:
    update_chain = []
    suitable_manifest_search_flag = True
    v = version_in_metadata
    while suitable_manifest_search_flag:
        # подходящие обновления для текущей версии
        suitable_manifest = _get_suitable_manifest(manifests, name_in_metadata, v)
        if suitable_manifest:
            update_chain.append(suitable_manifest)
            # теперь будем искать обновления для "обновлённой" версии
            v = suitable_manifest[1]
        else:
            suitable_manifest_search_flag = False
    return update_chain, len(update_chain) > 1


async def _update_info_base(ib_name, dry=False):
    """
    1. Получает тип конфигурации и её версию, выбирает подходящее обновление
    2. Блокирует фоновые задания и новые сеансы
    3. Принудительно завершает текущие сеансы
    4. Обновляет информационную базу
    5. Проверяет, есть ли ещё обновления, если есть, то возвращается на шаг №3
    6. Снимает блокировку фоновых заданий и сеансов
    """
    log.info(f'<{ib_name}> Initiate update')
    updatePath = settings.UPDATE_PATH
    result = core_types.InfoBaseUpdateTaskResult(ib_name, True)
    info_base_user, info_base_pwd = utils.get_info_base_credentials(ib_name)
    with cluster.ClusterControlInterface() as cci:
        try:
            # Получает тип конфигурации и её версию
            # TODO: подумать, как сделать получение метаданных асинхронным
            metadata = cci.get_info_base_metadata(ib_name, info_base_user, info_base_pwd)
        except pywintypes.com_error as e:
            # Если начало сеанса с информационной базой запрещено, то можно снять блокировку и попробывать ещё раз
            if e.excepinfo[5] == -2147467259:
                # TODO: подумать нужно ли это делать, или база заблокирована не просто так
                pass
            raise e
    name_in_metadata = metadata[0]
    version_in_metadata = get_version_from_string(metadata[1])
    # Получает манифесты всех обновлений в указанной директории
    path = os.path.join(updatePath, '**', '1cv8.mft')
    manifests = glob.glob(pathname=path, recursive=True)
    update_chain, is_multiupdate = _get_update_chain(manifests, name_in_metadata, version_in_metadata)
    # Использует отдельную переменную для версии для корректного вывода логов в цепочке обновлений
    current_version = version_in_metadata
    if is_multiupdate:
        chain_str = " -> ".join([str(manifest[1]) for manifest in itertools.chain([current_version], update_chain)])
        log.info(f'<{ib_name}> Created update chain [{chain_str}]')
    for selected_manifest in update_chain:
        log.info(f'<{ib_name}> Start update for [{name_in_metadata} {current_version}] -> [{selected_manifest[1]}]')
        selected_update_filename = selected_manifest[0].replace('1cv8.mft', '1cv8.cfu')
        # Код блокировки новых сеансов
        permission_code = "0000"
        # Формирует команду для обновления
        log_filename = os.path.join(settings.LOG_PATH, utils.get_ib_and_time_filename(ib_name, 'log'))
        # https://its.1c.ru/db/v838doc#bookmark:adm:TI000000530
        v8_command = \
            rf'"{utils.get_platform_full_path()}" ' \
            rf'DESIGNER /S {cluster.get_server_address()}\{ib_name} ' \
            rf'/N"{info_base_user}" /P"{info_base_pwd}" ' \
            rf'/Out {log_filename} -NoTruncate ' \
            rf'/UC "{permission_code}" ' \
            rf'/DisableStartupDialogs /DisableStartupMessages ' \
            rf'/UpdateCfg "{selected_update_filename}" -force /UpdateDBCfg -Dynamic- -Server'
        log.info(f'Created update command [{v8_command}]')
        if not dry:
            # Случайная пауза чтобы исключить проблемы с конкурентным доступом к файлу обновления в случае, 
            # если одновременно обновляются несколько ИБ с одинаковой конфигурацией и версией.
            # Ошибка совместного доступа к файлу '1cv8.cfu'. 32(0x00000020): 
            # Процесс не может получить доступ к файлу, так как этот файл занят другим процессом.
            await asyncio.sleep(random.randint(0, 10))
            # Обновляет информационную базу и конфигурацию БД
            await execute_v8_command(
                ib_name, v8_command, log_filename, permission_code
            )
            if is_multiupdate:
                # Если в цепочке несколько обновлений, то после каждого проверяет версию ИБ,
                # и продолжает только в случае, если ИБ обновилась.
                previous_version = current_version
                with cluster.ClusterControlInterface() as cci:
                    try:
                        metadata = cci.get_info_base_metadata(ib_name, info_base_user, info_base_pwd)
                    except pywintypes.com_error as e:
                        raise e
                current_version = get_version_from_string(metadata[1])
                if current_version == previous_version:
                    log.error(
                        f'<{ib_name}> Update [{name_in_metadata} {current_version}] -> [{selected_manifest[1]}] '
                        f'was not applied, next chain updates will not be applied'
                    )
                    result = core_types.InfoBaseUpdateTaskResult(ib_name, False)
        if not update_chain:
            log.info(f'<{ib_name}> No suitable update for [{name_in_metadata} {version_in_metadata}] was found')
    return result


async def update_info_base(ib_name: str, semaphore: asyncio.Semaphore) -> core_types.InfoBaseUpdateTaskResult:
    async with semaphore:
        try:
            return await utils.com_func_wrapper(_update_info_base, ib_name)
        except Exception:
            log.exception(f'<{ib_name}> Unknown exception occurred in coroutine')
            return core_types.InfoBaseUpdateTaskResult(ib_name, False)


def analyze_results(
    info_bases: List[str],
    update_result: List[core_types.InfoBaseUpdateTaskResult],
    update_datetime_start: datetime,
    update_datetime_finish: datetime,
):
    analyze_update_result(update_result, info_bases, update_datetime_start, update_datetime_finish)


async def main():
    try:
        info_bases = utils.get_info_bases()
        update_concurrency = settings.UPDATE_CONCURRENCY
        update_semaphore = asyncio.Semaphore(update_concurrency)
        log.info(f'<{log_prefix}> Asyncio semaphore initialized: {update_concurrency} update concurrency')
        update_datetime_start = datetime.now()
        update_results = await asyncio.gather(*[update_info_base(ib_name, update_semaphore) for ib_name in info_bases])
        update_datetime_finish = datetime.now()

        analyze_results(
            info_bases, 
            update_results, 
            update_datetime_start, 
            update_datetime_finish, 
        )

        log.info(f'<{log_prefix}> Done')
    except Exception as e:
        log.exception(f'<{log_prefix}> Unknown exception occured in main coroutine')


if __name__ == "__main__":
    if sys.version_info < (3, 10):
        asyncio.get_event_loop().run_until_complete(main())
    else:
        asyncio.run(main())
