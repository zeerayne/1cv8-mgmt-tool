import logging
from typing import List

from core.cluster.abc import ClusterControler
from core.cluster.models import V8CInfobase, V8CInfobaseShort
from core.cluster.utils import get_server_agent_address, get_server_agent_port

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


class ClusterCOMControler(ClusterControler):
    """
    Примечание: любые COM-объекты не могут быть переданы между потоками,
    и должны использоваться только в потоке, в котоорм были созданы
    """

    def __init__(self):
        try:
            self.V8COMConnector = win32com_client.Dispatch("V83.COMConnector")
        except pywintypes.com_error as e:
            raise e
        self.server = get_server_agent_address()
        self.agentPort = get_server_agent_port()
        self.clusterAdminName = settings.V8_CLUSTER_ADMIN_CREDENTIALS[0]
        self.clusterAdminPwd = settings.V8_CLUSTER_ADMIN_CREDENTIALS[1]
        self.infoBasesCredentials = settings.V8_INFOBASES_CREDENTIALS

    def get_agent_connection(self):
        if getattr(self, "agent_connection", None) is None:
            self.agent_connection = self.V8COMConnector.ConnectAgent(f"{self.server}:{self.agentPort}")
        return self.agent_connection

    def get_cluster(self):
        """
        Получает первый кластер из списка
        :param agent_connection: Соединение с агентом сервера
        :return: Объект IClusterInfo
        """
        agent_connection = self.get_agent_connection()
        if getattr(self, "cluster", None) is None:
            self.cluster = agent_connection.GetClusters()[0]
        return self.cluster

    def cluster_auth(self):
        """
        Авторизует соединение с агентом сервера для указанного кластера. Данные для авторизации берутся из настроек
        :param agent_connection: Соединение с агентом сервера
        :param cluster: Кластер
        :return: Объект IClusterInfo
        """
        agent_connection = self.get_agent_connection()
        cluster = self.get_cluster()
        agent_connection.Authenticate(cluster, self.clusterAdminName, self.clusterAdminPwd)
        return cluster

    def get_cluster_with_auth(self):
        if getattr(self, "cluster_with_auth", None) is None:
            self.cluster_with_auth = self.cluster_auth()
        return self.cluster_with_auth

    def get_working_process_connection(self):
        agent_connection = self.get_agent_connection()
        cluster = self.get_cluster_with_auth()

        working_process_0 = agent_connection.GetWorkingProcesses(cluster)[0]
        working_process_port = str(working_process_0.MainPort)
        working_process_connection = self.V8COMConnector.ConnectWorkingProcess(
            f"tcp://{self.server}:{working_process_port}"
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

    def _filter_infobase(self, info_bases: List, name: str):
        for ib in info_bases:
            if ib.Name.lower() == name.lower():
                return ib

    def _get_cluster_info_bases(self) -> List:
        working_process_connection = self.get_working_process_connection_with_info_base_auth()
        info_bases = working_process_connection.GetInfoBases()
        return info_bases

    def _get_info_base(self, name):
        info_bases = self._get_cluster_info_bases()
        return self._filter_infobase(info_bases, name)

    def get_cluster_info_bases(self) -> List[V8CInfobaseShort]:
        info_bases = self._get_cluster_info_bases()
        return [V8CInfobaseShort(name=ib.Name) for ib in info_bases]

    def get_info_base(self, name) -> V8CInfobase:
        com_infobase = self._get_info_base(name)
        return V8CInfobase(
            name=com_infobase.Name,
            db_server=com_infobase.dbServerName,
            dbms=com_infobase.DBMS,
            db_name=com_infobase.dbName,
            db_user=com_infobase.dbUser,
        )

    def get_cluster_info_bases_short(self, agent_connection, cluster):
        info_bases_short = agent_connection.GetInfoBases(cluster)
        return info_bases_short

    def _get_info_base_short(self, agent_connection, cluster, name: str):
        info_bases_short = self.get_cluster_info_bases_short(agent_connection, cluster)
        return self._filter_infobase(info_bases_short, name)

    def get_info_base_metadata(self, infobase: str, infobase_user: str, infobase_pwd: str):
        """
        Получает наименование и версию конфигурации
        :param infobase: Имя информационной базы
        :param infobase_user: Пользователь ИБ с правами администратора
        :param infobase_pwd: Пароль пользователя ИБ
        :return: tuple(Наименование, Версия информационной базы)
        """
        external_connection = self.V8COMConnector.Connect(
            f'Srvr="{self.server}";Ref="{infobase}";Usr="{infobase_user}";Pwd="{infobase_pwd}";'
        )
        version = external_connection.Metadata.Version
        name = external_connection.Metadata.Name
        del external_connection
        return name, version

    def lock_info_base(
        self,
        infobase: str,
        permission_code: str = "0000",
        message: str = "Выполняется обслуживание ИБ",
    ):
        """
        Блокирует фоновые задания и новые сеансы информационной базы
        :param infobase: имя информационной базы
        :param permission_code: Код доступа к информационной базе во время блокировки сеансов
        :param message: Сообщение будет выводиться при попытке установить сеанс с ИБ
        """
        infobase_com_obj = self._get_info_base(infobase)
        infobase_com_obj.ScheduledJobsDenied = True
        infobase_com_obj.SessionsDenied = True
        infobase_com_obj.PermissionCode = permission_code
        infobase_com_obj.DeniedMessage = message
        # TODO: необходима проверка, есть ли у рабочего процесса необходимые авторизационные данные для этой ИБ
        log.debug(
            f"<{infobase_com_obj.Name}> If process crashes after this message it means there is no correct credentials for infobase"
        )
        working_process_connection = self.get_working_process_connection_with_info_base_auth()
        working_process_connection.UpdateInfoBase(infobase_com_obj)
        log.debug(f"<{infobase_com_obj.Name}> Lock info base successfully")
        return infobase_com_obj

    def unlock_info_base(self, infobase: str):
        """
        Снимает блокировку фоновых заданий и сеансов информационной базы
        :param infobase: имя информационной базы
        """
        infobase_com_obj = self._get_info_base(infobase)
        infobase_com_obj.ScheduledJobsDenied = False
        infobase_com_obj.SessionsDenied = False
        infobase_com_obj.DeniedMessage = ""
        working_process_connection = self.get_working_process_connection_with_info_base_auth()
        working_process_connection.UpdateInfoBase(infobase_com_obj)
        log.debug(f"<{infobase_com_obj.Name}> Unlock info base successfully")
        return infobase_com_obj

    def terminate_info_base_sessions(self, infobase: str):
        """
        Принудительно завершает текущие сеансы информационной базы
        :param infobase: имя информационной базы
        """
        agent_connection = self.get_agent_connection()
        cluster_with_auth = self.get_cluster_with_auth()
        info_base_short = self._get_info_base_short(agent_connection, cluster_with_auth, infobase)
        info_base_sessions = agent_connection.GetInfoBaseSessions(cluster_with_auth, info_base_short)
        for session in info_base_sessions:
            agent_connection.TerminateSession(cluster_with_auth, session)
