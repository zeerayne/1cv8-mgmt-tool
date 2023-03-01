try:
    import pywintypes
except ImportError:
    from surrogate import surrogate

    surrogate("pywintypes").prepare()
    import pywintypes

    pywintypes.com_error = Exception

import logging

import core.models as core_models
from conf import settings
from core.exceptions import V8Exception

log = logging.getLogger(__name__)


def get_cluster_controller_class():
    from core.cluster.comcntr import ClusterCOMControler

    controller_class = ClusterCOMControler
    return controller_class


def get_server_agent_address() -> str:
    return settings.V8_SERVER_AGENT["address"]


def get_server_agent_port() -> str:
    return str(settings.V8_SERVER_AGENT["port"])


def get_ras_address() -> str:
    return settings.V8_RAS["address"]


def get_ras_port() -> str:
    return str(settings.V8_RAS["port"])


async def com_func_wrapper(func, ib_name: str, **kwargs) -> core_models.InfoBaseTaskResultBase:
    """
    Оборачивает функцию для обработки COM-ошибок
    :param func: функция, которая будет обёрнута
    :param ib_name: имя информационной базы
    :return: Массив ib_name, func_result
    """
    try:
        result = await func(ib_name, **kwargs)
    except pywintypes.com_error:
        log.exception(f"<{ib_name}> COM Error occured")
        # Если произошла ошибка, пытаемся снять блокировку ИБ
        try:
            cci = get_cluster_controller_class()()
            cci.unlock_info_base(ib_name)
        except pywintypes.com_error:
            log.exception(f"<{ib_name}> COM Error occured during handling another COM Error")
        # После разблокировки возвращаем неуспешный результат
        return core_models.InfoBaseTaskResultBase(ib_name, False)
    except V8Exception:
        return core_models.InfoBaseTaskResultBase(ib_name, False)
    return result
