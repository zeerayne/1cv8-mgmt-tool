import logging
from typing import Tuple

try:
    import pywintypes
    import win32com.client as win32com_client
except ImportError:
    from surrogate import surrogate

    surrogate("win32com.client").prepare()
    surrogate("pywintypes").prepare()
    import pywintypes
    import win32com.client as win32com_client

    pywintypes.com_error = Exception
    win32com_client.Dispatch = lambda i: None

from conf import settings

r"""
Для доступа к информационной базе из внешней программы используется COM объект COMConnector.
При установке платформы 1С в операционной системе автоматически регистрируется класс COMConnector.
Если по каким либо причинам регистрация не прошла, то его можно зарегистрировать вручную.

Если COMConnector не зарегистрирован в Windows, то при программном создании объекта будет появляться ошибка:
> Ошибка при вызове конструктора (COMObject): -2147221164(0x80040154): Класс не зарегистрирован.

Для того чтобы зарегистрировать ComConnector в 64 разрядной операционной системе Windows выполняется
команда: regsvr32 "C:\Program Files\1cv8\[version]\bin\comcntr.dll"
"""

log = logging.getLogger(__name__)


class FileCOMControler:
    """
    Примечание: любые COM-объекты не могут быть переданы между потоками,
    и должны использоваться только в потоке, в котоорм были созданы
    """

    def __init__(self):
        try:
            self.V8COMConnector = win32com_client.Dispatch("V83.COMConnector")
        except pywintypes.com_error as e:
            raise e

    def get_info_base_metadata(self, infobase: str, infobase_user: str, infobase_pwd: str) -> Tuple[str, str]:
        """
        Получает наименование и версию конфигурации
        :param infobase: Имя информационной базы
        :param infobase_user: Пользователь ИБ с правами администратора
        :param infobase_pwd: Пароль пользователя ИБ
        :return: tuple(Наименование, Версия информационной базы)
        """

        external_connection = self.V8COMConnector.Connect(
            f'File="{settings.V8_FILE_INFOBASES[infobase]}";Usr="{infobase_user}";Pwd="{infobase_pwd}";'
        )
        version = external_connection.Metadata.Version
        name = external_connection.Metadata.Name
        del external_connection
        return name, version
