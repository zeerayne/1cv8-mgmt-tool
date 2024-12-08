import textwrap
from core.cluster.models import V8CCluster
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
