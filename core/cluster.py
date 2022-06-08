import logging
from typing import List

try:
    import win32com.client as win32com_client
except ImportError:
    from core.surrogate import surrogate
    surrogate('win32com.client').prepare()
    import win32com.client as win32com_client

from conf import settings


r"""
Для доступа к информационной базе из внешней программы используется COM объект COMConnector. 
В зависимости от версии платформы используется V82.COMConnector или V83.COMConnector. При установке платформы 1С, 
операционной системе автоматически регистрируется класс COMConnector. 
Если по каким либо причинам регистрация не прошла, то его можно зарегистрировать вручную.
 
Если COMConnector не зарегистрирован в Windows, то при программном создании объекта будет появляться ошибка:
> Ошибка при вызове конструктора (COMObject): -2147221164(0x80040154): Класс не зарегистрирован.

Для того чтобы зарегистрировать ComConnector в 64 разрядной операционной системе Windows выполняется
команда: regsvr32 "C:\Program Files\1cv8\[version]\bin\comcntr.dll" 
"""


log = logging.getLogger(__name__)


class ClusterControlInterface:
    """
    Примечание: любые COM-объекты не могут быть переданы между потоками,
    и должны использоваться только в потоке, в котоорм были созданы
    """

    def __init__(self):
        # В зависимости от версии платформы используется V82.COMConnector или V83.COMConnector
        try:
            self.V8COMConnector = win32com_client.Dispatch("V83.COMConnector")
        except:
            self.V8COMConnector = win32com_client.Dispatch("V82.COMConnector")
        self.server = settings.V8_SERVER_AGENT["address"]
        self.agentPort = str(settings.V8_SERVER_AGENT["port"])
        self.clusterAdminName = settings.V8_CLUSTER_ADMIN_CREDENTIALS[0]
        self.clusterAdminPwd = settings.V8_CLUSTER_ADMIN_CREDENTIALS[1]
        self.infoBasesCredentials = settings.V8_INFO_BASES_CREDENTIALS

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        del self.V8COMConnector

    def get_agent_connection(self):
        agent_connection = self.V8COMConnector.ConnectAgent("{0}:{1}".format(self.server, self.agentPort))
        return agent_connection

    def get_cluster(self, agent_connection):
        """
        Получает первый кластер из списка
        :param agent_connection: Соединение с агентом сервера
        :return: Объект IClusterInfo
        """
        cluster = agent_connection.GetClusters()[0]
        return cluster

    def cluster_auth(self, agent_connection, cluster):
        """
        Авторизует соединение с агентом сервера для указанного кластера. Данные для авторизации берутся из настроек
        :param agent_connection: Соединение с агентом сервера
        :param cluster: Кластер
        """
        agent_connection.Authenticate(cluster, self.clusterAdminName, self.clusterAdminPwd)

    def get_cluster_with_auth(self, agent_connection):
        cluster = self.get_cluster(agent_connection)
        self.cluster_auth(agent_connection, cluster)
        return cluster

    def get_working_process_connection(self):
        agent_connection = self.get_agent_connection()
        cluster = self.get_cluster_with_auth(agent_connection)

        working_process_0 = agent_connection.GetWorkingProcesses(cluster)[0]
        working_process_port = str(working_process_0.MainPort)
        working_process_connection = self.V8COMConnector.ConnectWorkingProcess(
            'tcp://{0}:{1}'.format(self.server, working_process_port)
        )
        # Выполняет аутентификацию администратора кластера.
        # Администратор кластера должен быть аутентифицирован для создания в этом кластере новой информационной базы.
        working_process_connection.AuthenticateAdmin(self.clusterAdminName, self.clusterAdminPwd)
        return working_process_connection

    def get_working_process_connection_with_info_base_auth(self):
        working_process_connection = self.get_working_process_connection()
        # Административный доступ разрешен только к тем информационным базам,
        # в которых зарегистрирован пользователь с таким именем и он имеет право "Администратор".
        for c in self.infoBasesCredentials.values():
            working_process_connection.AddAuthentication(c[0], c[1])
        return working_process_connection

    def _get_info_base(self, info_bases: List, name: str):
        for ib in info_bases:
            if ib.Name.lower() == name.lower():
                return ib

    def get_info_bases(self, working_process_connection):
        info_bases = working_process_connection.GetInfoBases()
        return info_bases

    def get_info_base(self, working_process_connection, name):
        info_bases = self.get_info_bases(working_process_connection)
        return self._get_info_base(info_bases, name)

    def get_info_bases_short(self, agent_connection, cluster):
        info_bases_short = agent_connection.GetInfoBases(cluster)
        return info_bases_short

    def get_info_base_short(self, agent_connection, cluster, name: str):
        info_bases_short = self.get_info_bases_short(agent_connection, cluster)
        return self._get_info_base(info_bases_short, name)

    def get_info_base_metadata(self, info_base, info_base_user: str, info_base_pwd: str):
        """
        Получает наименование и версию конфигурации
        :param info_base: COM-Объект типа IInfoBaseShort или IInfoBaseInfo. Подойдёт любой объект, имеющий поле Name
        :param info_base_user: Пользователь ИБ с правами администратора
        :param info_base_pwd: Пароль пользователя ИБ
        :return: tuple(Наименование, Версия информационной базы)
        """
        external_connection = self.V8COMConnector.Connect(
            'Srvr="{0}";Ref="{1}";Usr="{2}";Pwd="{3}";'.format(self.server, info_base, info_base_user, info_base_pwd)
        )
        version = external_connection.Metadata.Version
        name = external_connection.Metadata.Name
        del external_connection
        return name, version

    def lock_info_base(self, working_process_connection, info_base, permission_code: str = '0000',
                       message: str = 'Выполняется обслуживание ИБ'):
        """
        Блокирует фоновые задания и новые сеансы информационной базы
        :param working_process_connection: Соединение с рабочим процессом
        :param info_base: COM-Объект класса IInfoBaseInfo
        :param permission_code: Код доступа к информационной базе во время блокировки сеансов
        :param message: Сообщение будет выводиться при попытке установить сеанс с ИБ
        """
        # TODO: необходима проверка, есть ли у рабочего процесса необходимые авторизационные данные для этой ИБ
        info_base.ScheduledJobsDenied = True
        info_base.SessionsDenied = True
        info_base.PermissionCode = permission_code
        info_base.DeniedMessage = message
        try:
            working_process_connection.UpdateInfoBase(info_base)
        except Exception as e:
            log.exception('[{0}] Lock info base exception'.format(info_base.Name))
        log.debug('[{0}] Lock info base successfully'.format(info_base.Name))

    def unlock_info_base(self, working_process_connection, info_base):
        """
        Снимает блокировку фоновых заданий и сеансов информационной базы
        :param working_process_connection: Соединение с рабочим процессом
        :param info_base: COM-Объект класса IInfoBaseInfo
        """
        info_base.ScheduledJobsDenied = False
        info_base.SessionsDenied = False
        info_base.DeniedMessage = ""
        working_process_connection.UpdateInfoBase(info_base)
        log.debug('[{0}] Unlock info base successfully'.format(info_base.Name))

    def terminate_info_base_sessions(self, agent_connection, cluster, info_base_short):
        """
        Принудительно завершает текущие сеансы информационной базы
        :param agent_connection: Соединение с агентом сервера
        :param cluster: Класер серверов
        :param info_base_short: COM-Объект класса IInfoBaseShort
        """
        info_base_sessions = agent_connection.GetInfoBaseSessions(cluster, info_base_short)
        for session in info_base_sessions:
            agent_connection.TerminateSession(cluster, session)
