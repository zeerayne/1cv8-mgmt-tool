from abc import ABC, abstractmethod
from typing import List


class V8CModel(ABC):
    @property
    @abstractmethod
    def keys(self) -> List[str]: ...

    @property
    @abstractmethod
    def id(self) -> str: ...

    def __init__(self, **kwargs):
        self.__dict__.update((k, v) for k, v in kwargs.items() if k in self.keys)


class V8CCluster(V8CModel):
    @property
    def id(self):
        return self.cluster

    @property
    def keys(self):
        return [
            "cluster",
            "host",
            "port",
            "name",
            "expiration_timeout",
            "lifetime_limit",
            "max_memory_size",
            "max_memory_time_limit",
            "security_level",
            "session_fault_tolerance_level",
            "load_balancing_mode",
            "errors_count_threshold",
            "kill_problem_processes",
            "kill_by_memory_with_dump",
        ]


class V8CInfobaseShort(V8CModel):
    @property
    def id(self):
        return self.infobase

    @property
    def keys(self):
        return [
            "infobase",
            "name",
            "descr",
        ]


class V8CInfobase(V8CInfobaseShort):
    @property
    def id(self):
        return self.infobase

    @property
    def keys(self):
        return [
            "infobase",
            "name",
            "dbms",
            "db_server",
            "db_name",
            "db_user",
            "security_level",
            "license_distribution",
            "scheduled_jobs_deny",
            "sessions_deny",
            "denied_from",
            "denied_message",
            "denied_parameter",
            "denied_to",
            "permission_code",
            "external_session_manager_connection_string",
            "external_session_manager_required",
            "security_profile_name",
            "safe_mode_security_profile_name",
            "reserve_working_processes",
            "descr",
            "disable_local_speech_to_text",
            "configuration_unload_delay_by_working_process_without_active_users",
            "minimum_scheduled_jobs_start_period_without_active_users",
            "maximum_scheduled_jobs_start_shift_without_active_users",
        ]
