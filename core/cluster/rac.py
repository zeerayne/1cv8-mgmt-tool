import logging

from core.cluster.abc import ClusterControler

log = logging.getLogger(__name__)


class ClusterRACControler(ClusterControler):

    def get_cluster_info_bases(self):
        """
        Получает список всех ИБ из кластера
        """
        ...


    def lock_info_base(self, infobase: str, permission_code: str, message: str):
        """
        Блокирует фоновые задания и новые сеансы информационной базы
        :param infobase: имя информационной базы
        :param permission_code: Код доступа к информационной базе во время блокировки сеансов
        :param message: Сообщение будет выводиться при попытке установить сеанс с ИБ
        """
        ...


    def unlock_info_base(self, infobase: str):
        """
        Снимает блокировку фоновых заданий и сеансов информационной базы
        :param infobase: имя информационной базы
        """
        ...


    def terminate_info_base_sessions(self, infobase: str):
        """
        Принудительно завершает текущие сеансы информационной базы
        :param infobase: имя информационной базы
        """
        ...


    def get_info_base(self, infobase: str):
        """
        Получает сведения об ИБ из кластера
        :param infobase: имя информационной базы
        """
        ...


"""
Use:

        rac cluster [command] [options] [arguments]

Shared options:

    --version | -v
        get the utility version

    --help | -h | -?
        display brief utility description

Shared arguments:

    <host>[:<port>]
        administration server address (default: localhost:1545)

Mode:

    cluster
        Server cluster administration mode

Commands:

    admin
        management of cluster administrators

        Additional commands:
            list
                receipt of the cluster administrator list

            register
                adding a new cluster administrator

                --name=<name>
                    (required) administrator name

                --pwd=<name>
                    administrator password in case of password authentication

                --descr=<descr>
                    description of the administrator

                --auth=pwd[,os]
                    available authentication methods:
                        pwd - using the user name and password
                        os - authentication using OS

                --os-user=<name>
                    OS user name

                --agent-user=<name>
                    name of the cluster agent administrator

                --agent-pwd=<pwd>
                    password of the cluster agent administrator

            remove
                deleting the cluster administrator

                --name=<name>
                    (required) name of the cluster administrator

        --cluster=<uuid>
            (required) server cluster identifier

        --cluster-user=<name>
            name of the cluster administrator

        --cluster-pwd=<pwd>
            password of the cluster administrator

    info
        receipt of cluster information

        --cluster=<uuid>
            (required) server cluster identifier

    list
        receipt of the cluster information list

    insert
        new cluster registration

        --host=<host>
            (required) name (or IP-address) of the computer where
            the cluster registry and the main cluster manager process are located

        --port=<port>
            (required) main port of the main manager

        --name=<name>
            cluster name (presentation)

        --expiration-timeout=<seconds>
            forced termination time (seconds)

        --lifetime-limit=<seconds>
            restart time of cluster working processes (seconds)

        --max-memory-size=<Kb>
            maximum virtual address space (KB),
            used by the working process

        --max-memory-time-limit=<seconds>
            maximum period of exceeding critical memory limit (seconds)

        --security-level=<level>
            connection security level

        --session-fault-tolerance-level=<level>
            fault-tolerance level

        --load-balancing-mode=performance|memory
            load balancing mode
                performance - priority by available performance
                memory - priority by available memory

        --errors-count-threshold=<percentage>
            server errors threshold (percentage)

        --kill-problem-processes=<yes/no>
            terminate corrupted processes

        --kill-by-memory-with-dump=<yes/no>
            create process dump when maximum memory amount is exceeded

        --agent-user=<name>
            name of the cluster agent administrator

        --agent-pwd=<pwd>
            password of the cluster agent administrator

    update
        cluster parameter update

        --cluster=<uuid>
            (required) server cluster identifier

        --name=<name>
            cluster name (presentation)

        --expiration-timeout=<seconds>
            forced termination time (seconds)

        --lifetime-limit=<seconds>
            restart time of cluster working processes (seconds)

        --max-memory-size=<Kb>
            maximum virtual address space (KB),
            used by the working process

        --max-memory-time-limit=<seconds>
            maximum period of exceeding critical memory limit (seconds)

        --security-level=<level>
            connection security level

        --session-fault-tolerance-level=<level>
            fault-tolerance level

        --load-balancing-mode=performance|memory
            load balancing mode
                performance - priority by available performance
                memory - priority by available memory

        --errors-count-threshold=<percentage>
            server errors threshold (percentage)

        --kill-problem-processes=<yes/no>
            terminate corrupted processes

        --kill-by-memory-with-dump=<yes/no>
            create process dump when maximum memory amount is exceeded

        --agent-user=<name>
            name of the cluster agent administrator

        --agent-pwd=<pwd>
            password of the cluster agent administrator

    remove
        deleting the cluster

        --cluster=<uuid>
            (required) server cluster identifier

        --cluster-user=<name>
            name of the cluster administrator

        --cluster-pwd=<pwd>
            password of the cluster administrator


./rac cluster admin list --cluster-user=Администратор --cluster=b930e651-0160-47c6-aeae-68b8ed937120 ras:1545
name    : Администратор
auth    : pwd
os-user :
descr   :

./rac cluster info --cluster=b930e651-0160-47c6-aeae-68b8ed937120 ras:1545
cluster                       : b930e651-0160-47c6-aeae-68b8ed937120
host                          : ragent
port                          : 1541
name                          : "Local cluster"
expiration-timeout            : 60
lifetime-limit                : 0
max-memory-size               : 0
max-memory-time-limit         : 0
security-level                : 0
session-fault-tolerance-level : 0
load-balancing-mode           : performance
errors-count-threshold        : 0
kill-problem-processes        : 1
kill-by-memory-with-dump      : 0

./rac cluster list ras:1545
cluster                       : b930e651-0160-47c6-aeae-68b8ed937120
host                          : ragent
port                          : 1541
name                          : "Local cluster"
expiration-timeout            : 60
lifetime-limit                : 0
max-memory-size               : 0
max-memory-time-limit         : 0
security-level                : 0
session-fault-tolerance-level : 0
load-balancing-mode           : performance
errors-count-threshold        : 0
kill-problem-processes        : 1
kill-by-memory-with-dump      : 0
"""
"""
./rac infobase summary list --cluster-user=Администратор --cluster=b930e651-0160-47c6-aeae-68b8ed937120 ras:1545


Use:

        rac infobase [command] [options] [arguments]

Shared options:

    --version | -v
        get the utility version

    --help | -h | -?
        display brief utility description

Shared arguments:

    <host>[:<port>]
        administration server address (default: localhost:1545)

Mode:

    infobase
        Infobase administration mode

Parameters:

    --cluster=<uuid>
        (required) server cluster identifier

    --cluster-user=<name>
        name of the cluster administrator

    --cluster-pwd=<pwd>
        password of the cluster administrator

Commands:

    info
        receiving the information about the infobase

        --infobase=<uuid>
            (required) infobase identifier

        --infobase-user=<name>
            name of the infobase administrator

        --infobase-pwd=<pwd>
            password of the infobase administrator

    summary
        management of brief information on infobases

        Additional commands:
            info
                receiving brief information on the infobase

                --infobase=<uuid>
                    (required) infobase identifier

            list
                receiving the list of brief information on infobases

            update
                updating brief information on the infobase

                --infobase=<uuid>
                    (required) infobase identifier

                --descr=<descr>
                    infobase description

    create
        infobase creation

        --create-database
            Create database when creating infobase

        --name=<name>
            (required) name of infobase

        --dbms=MSSQLServer|PostgreSQL|IBMDB2|OracleDatabase
            (required) type of the Database Management System where the infobase is located:
                MSSQLServer - MS SQL Server
                PostgreSQL - PostgreSQL
                IBMDB2 - IBM DB2
                OracleDatabase - Oracle Database

        --db-server=<host>
            (required) the name of the database server

        --db-name=<name>
            (required) database name

        --locale=<locale>
            (required) identifier of national settings of the infobase

        --db-user=<name>
            database administrator name

        --db-pwd=<pwd>
            database administrator password

        --descr=<descr>
            infobase description

        --date-offset=<offset>
            date offset in the infobase

        --security-level=<level>
            infobase connection security level

        --scheduled-jobs-deny=on|off
            scheduled job lock management
                on - scheduled job execution prohibited
                off - scheduled job execution permitted

        --license-distribution=deny|allow
            management of licenses granting by 1C:Enterprise server
                deny - licensing is forbidden
                allow - licensing is allowed

    update
        updating information on infobase

        --infobase=<uuid>
            (required) infobase identifier

        --infobase-user=<name>
            name of the infobase administrator

        --infobase-pwd=<pwd>
            password of the infobase administrator

        --dbms=MSSQLServer|PostgreSQL|IBMDB2|OracleDatabase
            type of the Database Management System where the infobase is located:
                MSSQLServer - MS SQL Server
                PostgreSQL - PostgreSQL
                IBMDB2 - IBM DB2
                OracleDatabase - Oracle Database

        --db-server=<host>
            the name of the database server

        --db-name=<name>
            database name

        --db-user=<name>
            database administrator name

        --db-pwd=<pwd>
            database administrator password

        --descr=<descr>
            infobase description

        --denied-from=<date>
            start of the time interval within which the session lock mode is enabled

        --denied-message=<msg>
            message displayed upon session lock violation

        --denied-parameter=<string>
            session lock parameter

        --denied-to=<date>
            end of the time interval within which the session lock mode is enabled

        --permission-code=<string>
            access code that allows the session to start in spite of enabled session lock

        --sessions-deny=on|off
            session lock mode management
                on - mode of session start lock enabled
                off - mode of session start lock disabled

        --scheduled-jobs-deny=on|off
            scheduled job lock management
                on - scheduled job execution prohibited
                off - scheduled job execution permitted

        --license-distribution=deny|allow
            management of licenses granting by 1C:Enterprise server
                deny - licensing is forbidden
                allow - licensing is allowed

        --external-session-manager-connection-string=<connect-string>
            external session management parameter

        --external-session-manager-required=yes|no
            external session management required
                yes - external session management is a must
                no - external session management is optional

        --reserve-working-processes=yes|no
            Workflow backup
                yes - Workflow backup is enabled
                no - Workflow backup is disabled

        --security-profile-name=<name>
            infobase security profile

        --safe-mode-security-profile-name=<name>
            external code security profile

    drop
        remote infobase mode

        --infobase=<uuid>
            (required) infobase identifier

        --infobase-user=<name>
            name of the infobase administrator

        --infobase-pwd=<pwd>
            password of the infobase administrator

        --drop-database
            delete database upon deleting infobase

        --clear-database
            clear database upon deleting infobase


./rac infobase create --create-database --name=infobase01 --dbms=MSSQLServer --db-server=db --db-name=infobase01 --locale=ru --db-user=sa --db-pwd=supersecretpassword --cluster-user=Администратор --cluster=b930e651-0160-47c6-aeae-68b8ed937120 ras:1545
./rac infobase create --create-database --name=infobase01 --dbms=PostgreSQL --db-server=db --db-name=infobase01 --locale=ru --db-user=postgres --db-pwd=supersecretpassword --cluster-user=Администратор --cluster=b930e651-0160-47c6-aeae-68b8ed937120 ras:1545
./rac infobase create --create-database --name=infobase02 --dbms=PostgreSQL --db-server=db --db-name=infobase02 --locale=ru --db-user=postgres --db-pwd=supersecretpassword --cluster-user=Администратор --cluster=b930e651-0160-47c6-aeae-68b8ed937120 ras:1545
---
infobase : 9046c0db-1939-42a7-9b2d-f0370ca950df
---
./rac infobase summary list --cluster-user=Администратор --cluster=b930e651-0160-47c6-aeae-68b8ed937120 ras:1545
---
server_addr=tcp://ragent:1540 descr=32(0x00000020): Broken pipe line=1470 file=src/rtrsrvc/src/DataExchangeTcpClientImpl.cpp
---
infobase : 01c55c12-0f4c-4101-8113-7707d450e83c
name     : infobase01
descr    :

infobase : 9046c0db-1939-42a7-9b2d-f0370ca950df
name     : infobase02
descr    :
"""

"""
Use:

        rac session [command] [options] [arguments]

Shared options:

    --version | -v
        get the utility version

    --help | -h | -?
        display brief utility description

Shared arguments:

    <host>[:<port>]
        administration server address (default: localhost:1545)

Mode:

    session
        Infobase session administration mode

Parameters:

    --cluster=<uuid>
        (required) server cluster identifier

    --cluster-user=<name>
        name of the cluster administrator

    --cluster-pwd=<pwd>
        password of the cluster administrator

Commands:

    info
        receiving information on the session

        --session=<uuid>
            (required) infobase session identifier

        --licenses
            displaying information on licenses granted to the session

    list
        receiving the session information list

        --infobase=<uuid>
            infobase identifier

        --licenses
            displaying information on licenses granted to the session

    terminate
        Forced termination of the session

        --session=<uuid>
            (required) infobase session identifier

        --error-message=<string>
            Session termination reason message

    interrupt-current-server-call
        current server call termination

        --session=<uuid>
            (required) infobase session identifier

        --error-message=<string>
            termination cause message
"""
