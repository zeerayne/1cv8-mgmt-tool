from abc import ABC, abstractmethod
from typing import List

from conf import settings
from core.cluster.models import V8CInfobase, V8CInfobaseShort


class ClusterControler(ABC):
    @abstractmethod
    def get_cluster_info_bases(self) -> List[V8CInfobaseShort]:
        """
        Получает список всех ИБ из кластера
        """
        ...

    @abstractmethod
    def lock_info_base(self, infobase: str, permission_code: str, message: str):
        """
        Блокирует фоновые задания и новые сеансы информационной базы
        :param infobase: имя информационной базы
        :param permission_code: Код доступа к информационной базе во время блокировки сеансов
        :param message: Сообщение будет выводиться при попытке установить сеанс с ИБ
        """
        ...

    @abstractmethod
    def unlock_info_base(self, infobase: str):
        """
        Снимает блокировку фоновых заданий и сеансов информационной базы
        :param infobase: имя информационной базы
        """
        ...

    @abstractmethod
    def terminate_info_base_sessions(self, infobase: str):
        """
        Принудительно завершает текущие сеансы информационной базы
        :param infobase: имя информационной базы
        """
        ...

    @abstractmethod
    def get_info_base(self, infobase: str) -> V8CInfobase:
        """
        Получает сведения об ИБ из кластера
        :param infobase: имя информационной базы
        """
        ...

    def get_info_bases(self) -> List[str]:
        """
        Получает имена всех ИБ, кроме указанных в списке V8_INFOBASES_EXCLUDE
        Если список V8_INFOBASES_ONLY не пустой, получает список ИБ, указанных в этом списке и присутствующих в кластере
        :return: массив с именами ИБ
        """
        info_bases_obj = self.get_cluster_info_bases()
        info_bases_raw = [ib.name for ib in info_bases_obj]
        if settings.V8_INFOBASES_ONLY:
            info_bases = list(
                filter(
                    lambda ib: ib.lower() in [ib_only.lower() for ib_only in settings.V8_INFOBASES_ONLY],
                    info_bases_raw,
                )
            )
        else:
            info_bases = list(
                filter(
                    lambda ib: ib.lower() not in [ib_exclude.lower() for ib_exclude in settings.V8_INFOBASES_EXCLUDE],
                    info_bases_raw,
                )
            )
        return info_bases
