import textwrap
from core.cluster.models import V8CCluster, V8CInfobase
from core.cluster.rac import ClusterRACControler


def test_cluster_rac_control_interface_parse_cluster():
    """
    `_rac_output_to_object` parse cluster object from rac output correctly
    """
    reference_object = V8CCluster(
        cluster="ceef02b4-da53-41bb-8332-fdc8fa7db83a",
        host="1c01",
        port="1541",
        name="Главный кластер",
        expiration_timeout="0",
        lifetime_limit="86400",
        max_memory_size="0",
        max_memory_time_limit="0",
        security_level="0",
        session_fault_tolerance_level="0",
        load_balancing_mode="performance",
        errors_count_threshold="0",
        kill_problem_processes="0",
        kill_by_memory_with_dump="0",
    )
    cluster_output = textwrap.dedent(
        """cluster                       : ceef02b4-da53-41bb-8332-fdc8fa7db83a
        host                          : 1c01
        port                          : 1541
        name                          : "Главный кластер"
        expiration-timeout            : 0
        lifetime-limit                : 86400
        max-memory-size               : 0
        max-memory-time-limit         : 0
        security-level                : 0
        session-fault-tolerance-level : 0
        load-balancing-mode           : performance
        errors-count-threshold        : 0
        kill-problem-processes        : 0
        kill-by-memory-with-dump      : 0

        cluster                                   : 167b70e8-31d3-40ce-a06f-0bf091b04fb3
        host                                      : ragent
        port                                      : 1541
        name                                      : "Local cluster"
        expiration-timeout                        : 60
        lifetime-limit                            : 0
        max-memory-size                           : 0
        max-memory-time-limit                     : 0
        security-level                            : 0
        session-fault-tolerance-level             : 0
        load-balancing-mode                       : performance
        errors-count-threshold                    : 0
        kill-problem-processes                    : 1
        kill-by-memory-with-dump                  : 0
        allow-access-right-audit-events-recording : 0
        ping-period                               : 0
        ping-timeout                              : 0

        """
    )
    constructed_object = ClusterRACControler()._rac_output_to_object(cluster_output, V8CCluster)
    assert constructed_object == reference_object


def test_cluster_rac_control_interface_parse_infobase():
    """
    `_rac_output_to_object` parse infobase object from rac output correctly
    """
    reference_object = V8CInfobase(
        infobase="f3466741-0208-4680-a9d3-21f16672048f",
        name="buh",
        dbms="MSSQLServer",
        db_server="10.0.0.0",
        db_name="buh",
        db_user="sa",
        security_level="0",
        license_distribution="allow",
        scheduled_jobs_deny="off",
        sessions_deny="off",
        denied_from="2020-09-12T18:49:18",
        denied_message="",
        denied_parameter="",
        denied_to="2020-09-12T18:50:18",
        permission_code="0000",
        external_session_manager_connection_string="",
        external_session_manager_required="no",
        security_profile_name="",
        safe_mode_security_profile_name="",
        reserve_working_processes="no",
        descr="Бухгалтерия",
        disable_local_speech_to_text="no",
        configuration_unload_delay_by_working_process_without_active_users="0",
        minimum_scheduled_jobs_start_period_without_active_users="0",
        maximum_scheduled_jobs_start_shift_without_active_users="0",
    )
    cluster_output = textwrap.dedent(
        """infobase                                                           : f3466741-0208-4680-a9d3-21f16672048f
        name                                                               : buh
        dbms                                                               : MSSQLServer
        db-server                                                          : 10.0.0.0
        db-name                                                            : buh
        db-user                                                            : sa
        security-level                                                     : 0
        license-distribution                                               : allow
        scheduled-jobs-deny                                                : off
        sessions-deny                                                      : off
        denied-from                                                        : 2020-09-12T18:49:18
        denied-message                                                     :
        denied-parameter                                                   :
        denied-to                                                          : 2020-09-12T18:50:18
        permission-code                                                    : "0000"
        external-session-manager-connection-string                         :
        external-session-manager-required                                  : no
        security-profile-name                                              :
        safe-mode-security-profile-name                                    :
        reserve-working-processes                                          : no
        descr                                                              : "Бухгалтерия"
        disable-local-speech-to-text                                       : no
        configuration-unload-delay-by-working-process-without-active-users : 0
        minimum-scheduled-jobs-start-period-without-active-users           : 0
        maximum-scheduled-jobs-start-shift-without-active-users            : 0

        """
    )
    constructed_object = ClusterRACControler()._rac_output_to_object(cluster_output, V8CInfobase)
    assert constructed_object == reference_object
