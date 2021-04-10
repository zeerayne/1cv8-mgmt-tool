import re
import glob
import logging
import pywintypes
import settings
from core.cluster import ClusterControlInterface
from core.process import execute_v8_command, execute_in_threadpool
from core.common import get_platform_full_path, get_formatted_current_datetime, \
    com_func_wrapper, get_info_bases, get_info_base_credentials, get_server_address
from core.version import get_version_from_string

server = get_server_address()
logPath = settings.LOG_PATH
updatePath = settings.UPDATE_PATH


def _find_suitable_manifests(manifests, name_in_metadata, version_in_metadata):
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


def _get_suitable_manifest(manifests, name_in_metadata, version_in_metadata):
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


def _get_update_chain(manifests, name_in_metadata, version_in_metadata):
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


def _update_info_base(ib_name):
    """
    1. Получает тип конфигурации и её версию, выбирает подходящее обновление
    2. Блокирует фоновые задания и новые сеансы
    3. Принудительно завершает текущие сеансы
    4. Обновляет информационную базу
    5. Проверяет, есть ли ещё обновления, если есть, то возвращается на шаг №3
    6. Снимает блокировку фоновых заданий и сеансов
    """
    logging.info('[%s] Initiate update' % ib_name)
    result = True
    with ClusterControlInterface() as cci:
        info_base_user, info_base_pwd = get_info_base_credentials(ib_name)
        # Получает тип конфигурации и её версию
        try:
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
        path = updatePath + "**\\1cv8.mft"
        manifests = glob.glob(pathname=path, recursive=True)
        update_chain, is_multiupdate = _get_update_chain(manifests, name_in_metadata, version_in_metadata)
        # Использует отдельную переменную для версии для корректного вывода логов в цепочке обновлений
        current_version = version_in_metadata
        if is_multiupdate:
            chain_str = " -> ".join([str(manifest[1]) for manifest in update_chain])
            logging.info('[%s] Created update chain [%s]' % (ib_name, chain_str))
        for selected_manifest in update_chain:
            logging.info('[%s] Start update for [%s %s] -> [%s]' %
                        (ib_name, name_in_metadata, current_version, selected_manifest[1])
                        )
            selected_update_filename = selected_manifest[0].replace('1cv8.mft', '1cv8.cfu')
            # Код блокировки новых сеансов
            permission_code = "0000"
            # Формирует команду для обновления
            time_str = get_formatted_current_datetime()
            ib_and_time_str = ib_name + '_' + time_str
            log_filename = logPath + ib_and_time_str + '.log'
            v8_command = \
                '"' + get_platform_full_path() + '" ' \
                'DESIGNER /S ' + server + '\\' + ib_name + ' ' \
                '/N"' + info_base_user + '" /P"' + info_base_pwd + '" ' \
                '/Out ' + log_filename + ' -NoTruncate ' \
                '/UC "' + permission_code + '" ' \
                '/UpdateCfg "' + selected_update_filename + '" /UpdateDBCfg -Server -v1'
            # Обновляет информационную базу и конфигурацию БД
            execute_v8_command(
                ib_name, v8_command, log_filename, permission_code
            )
            if is_multiupdate:
                # Если в цепочке несколько обновлений, то после каждого проверяет версию ИБ,
                # и продолжает только в случае, если ИБ обновилась.
                previous_version = current_version
                metadata = cci.get_info_base_metadata(ib_name, info_base_user, info_base_pwd)
                current_version = get_version_from_string(metadata[1])
                if current_version == previous_version:
                    logging.error('[%s] Update [%s %s] -> [%s] was not applied, next chain updates will not be applied' %
                                (ib_name, name_in_metadata, current_version, selected_manifest[1])
                                )
                    result = False
        if not update_chain:
            logging.info('[%s] No suitable update for [%s %s] was found' %
                        (ib_name, name_in_metadata, version_in_metadata)
                        )
            logging.info('[%s] Skip update' % ib_name)
    return result


def update_info_base(ib_name):
    try:
        return com_func_wrapper(_update_info_base, ib_name)
    except Exception as e:
        logging.exception('[{0}] Unknown exception occurred in thread'.format(ib_name))
        return ib_name, False


if __name__ == "__main__":
    try:
        info_bases = get_info_bases()
        updateThreads = settings.UPDATE_THREADS
        result = execute_in_threadpool(update_info_base, info_bases, updateThreads)
        logging.info('Done')
    except Exception as e:
        logging.exception('Unknown exception occured in main thread')
