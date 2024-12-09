import subprocess
import logging

from typing import List, Type

from conf import settings
from core.exceptions import RACException
from core.cluster.abc import ClusterControler
from core.cluster.models import V8CModel, V8CCluster, V8CInfobaseShort, V8CInfobase, V8CSession

log = logging.getLogger(__name__)


class ClusterRACControler(ClusterControler):
    def __init__(self):
        self.ras_host = settings.V8_RAS["address"]
        self.ras_port = settings.V8_RAS["port"]
        self.cluster_admin_name = settings.V8_CLUSTER_ADMIN_CREDENTIALS[0]
        self.cluster_admin_pwd = settings.V8_CLUSTER_ADMIN_CREDENTIALS[1]
        self.infobases_credentials = settings.V8_INFOBASES_CREDENTIALS

    def _get_rac_exec_path(self):
        # TODO: поддержка windows/linux
        # TODO: поддержка сценариев, когда утилита не включена в PATH
        return "rac"

    def _rac_output_to_objects(self, output: str, obj_class: Type[V8CModel]) -> List[V8CModel]:
        objects = []
        lines = [line for line in output.splitlines()]
        kw = dict()
        for line in lines:
            if not line.strip():
                objects.append(obj_class(**kw))
                kw.clear()
                continue
            key, value = line.split(":", maxsplit=1)
            kw.setdefault(key.replace("-", "_").strip(), value.strip().strip('"'))
        return objects

    def _rac_output_to_object(self, output: str, obj_class: Type[V8CModel]) -> V8CModel:
        return self._rac_output_to_objects(output, obj_class)[0]

    def _rac_call(self, command: str) -> str:
        call_str = f"{self._get_rac_exec_path()} {self.ras_host}:{self.ras_port} {command} ; exit 0"
        log.debug(f"Created rac command [{call_str}]")
        try:
            out = subprocess.check_output(call_str, stderr=subprocess.STDOUT, shell=True)
            out = out.decode("utf-8")
        except subprocess.CalledProcessError as e:
            raise RACException() from e
        return out

    def _get_clusters(self) -> List[V8CCluster]:
        cmd = "cluster list"
        output = self._rac_call(cmd)
        return self._rac_output_to_objects(output, V8CCluster)

    def _get_cluster(self, name=None) -> V8CCluster:
        return self._get_clusters()[0]

    def _with_cluster_auth(self) -> str:
        cluster = self._get_cluster()
        auth = f"--cluster={cluster.id}"
        if self.cluster_admin_name:
            auth += f" --cluster-user={self.cluster_admin_name}"
        if self.cluster_admin_pwd:
            auth += f" --cluster-pwd={self.cluster_admin_pwd}"
        return auth

    def _with_infobase_auth(self, infobase: V8CInfobaseShort):
        auth = f"--infobase={infobase.id}"
        default = self.infobases_credentials.get("default")
        creds = self.infobases_credentials.get(infobase.name, default)
        if creds[0]:
            auth += f" --infobase-user={creds[0]}"
        if creds[1]:
            auth += f" --infobase-pwd={creds[1]}"
        return auth

    def _filter_infobase(self, infobases: List[V8CInfobaseShort], name: str):
        for ib in infobases:
            if ib.name.lower() == name.lower():
                return ib

    def _get_infobase_short(self, infobase_name: str) -> V8CInfobaseShort:
        return self._filter_infobase(self.get_cluster_info_bases(), infobase_name)

    def _get_infobase_sessions(self, infobase: V8CInfobaseShort) -> List[V8CSession]:
        cmd = f"session list {self._with_cluster_auth()} --infobase={infobase.id}"
        output = self._rac_call(cmd)
        return self._rac_output_to_objects(output, V8CSession)

    def _terminate_session(self, session: V8CSession):
        cmd = f"session terminate {self._with_cluster_auth()} --session={session.id}"
        self._rac_call(cmd)

    def get_cluster_info_bases(self) -> List[V8CInfobaseShort]:
        """
        Получает список всех ИБ из кластера
        """
        cmd = f"infobase summary list {self._with_cluster_auth()} "
        output = self._rac_call(cmd)
        return self._rac_output_to_objects(output, V8CInfobaseShort)

    def lock_info_base(self, infobase: str, permission_code: str, message: str):
        """
        Блокирует фоновые задания и новые сеансы информационной базы
        :param infobase: имя информационной базы
        :param permission_code: Код доступа к информационной базе во время блокировки сеансов
        :param message: Сообщение будет выводиться при попытке установить сеанс с ИБ
        """
        ib = self._get_infobase_short(infobase)
        cmd = f"infobase update {self._with_cluster_auth()} {self._with_infobase_auth(ib)} --sessions-deny=on --scheduled-jobs-deny=on --permission-code={permission_code} --denied-message={message}"
        self._rac_call(cmd)

    def unlock_info_base(self, infobase: str):
        """
        Снимает блокировку фоновых заданий и сеансов информационной базы
        :param infobase: имя информационной базы
        """
        ib = self._get_infobase_short(infobase)
        cmd = f"infobase update {self._with_cluster_auth()} {self._with_infobase_auth(ib)} --sessions-deny=off --scheduled-jobs-deny=off"
        self._rac_call(cmd)

    def terminate_info_base_sessions(self, infobase: str):
        """
        Принудительно завершает текущие сеансы информационной базы
        :param infobase: имя информационной базы
        """
        ib = self._get_infobase_short(infobase)
        sessions = self._get_infobase_sessions(ib)
        for s in sessions:
            self._terminate_session(s)

    def get_info_base(self, infobase: str) -> V8CInfobase:
        """
        Получает сведения об ИБ из кластера
        :param infobase: имя информационной базы
        """
        ib = self._get_infobase_short(infobase)
        cmd = f"infobase info {self._with_cluster_auth()} {self._with_infobase_auth(ib)}"
        output = self._rac_call(cmd)
        return self._rac_output_to_object(output, V8CInfobase)
