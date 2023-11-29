import asyncio
import random
from textwrap import dedent
from unittest.mock import AsyncMock, Mock, PropertyMock, mock_open

import pytest
from packaging.version import Version
from pytest_mock import MockerFixture

from core import models as core_models
from utils.postgres import POSTGRES_NAME

random.seed(0)


@pytest.fixture()
def infobases():
    return ["infobase_test_01", "infobase_test_02", "infobase_test_03"]


@pytest.fixture()
def file_infobases():
    return ["file_infobase_test_01", "file_infobase_test_02", "file_infobase_test_03"]


@pytest.fixture()
def mock_file_infobases(mocker: MockerFixture, file_infobases):
    file_infobases_dict = {i: f"/path/to/file/infobase/{i}" for i in file_infobases}
    mock_file_infobases = mocker.patch(
        "conf.settings.V8_FILE_INFOBASES", new_callable=PropertyMock(return_value=file_infobases_dict)
    )
    return mock_file_infobases


@pytest.fixture()
def infobase(infobases):
    return infobases[0]


@pytest.fixture()
def file_infobase(file_infobases):
    return file_infobases[0]


@pytest.fixture()
def success_base_result(infobases):
    return [
        core_models.InfoBaseTaskResultBase(
            infobase_name=ib,
            succeeded=True,
        )
        for ib in infobases
    ]


@pytest.fixture()
def failed_base_result(infobases):
    return [
        core_models.InfoBaseTaskResultBase(
            infobase_name=ib,
            succeeded=False,
        )
        for ib in infobases
    ]


@pytest.fixture()
def mixed_base_result(infobases):
    succeeded = True
    return [
        core_models.InfoBaseTaskResultBase(
            infobase_name=ib,
            succeeded=(succeeded := not succeeded),
        )
        for ib in infobases
    ]


@pytest.fixture()
def success_backup_result(infobases):
    return [
        core_models.InfoBaseBackupTaskResult(infobase_name=ib, succeeded=True, backup_filename=f"./{ib}.testbackup")
        for ib in infobases
    ]


@pytest.fixture()
def failed_backup_result(infobases):
    return [
        core_models.InfoBaseBackupTaskResult(
            infobase_name=ib,
            succeeded=False,
        )
        for ib in infobases
    ]


@pytest.fixture()
def mixed_backup_result(infobases):
    succeeded = True
    return [
        core_models.InfoBaseBackupTaskResult(
            infobase_name=ib,
            succeeded=(succeeded := not succeeded),
            backup_filename=f"./{ib}.testbackup" if succeeded else "",
        )
        for ib in infobases
    ]


@pytest.fixture()
def success_maintenance_result(infobases):
    return [core_models.InfoBaseMaintenanceTaskResult(infobase_name=ib, succeeded=True) for ib in infobases]


@pytest.fixture()
def failed_maintenance_result(infobases):
    return [
        core_models.InfoBaseMaintenanceTaskResult(
            infobase_name=ib,
            succeeded=False,
        )
        for ib in infobases
    ]


@pytest.fixture()
def mixed_maintenance_result(infobases):
    succeeded = True
    return [
        core_models.InfoBaseMaintenanceTaskResult(infobase_name=ib, succeeded=(succeeded := not succeeded))
        for ib in infobases
    ]


@pytest.fixture()
def success_update_result(infobases):
    return [core_models.InfoBaseUpdateTaskResult(infobase_name=ib, succeeded=True) for ib in infobases]


@pytest.fixture()
def failed_update_result(infobases):
    return [
        core_models.InfoBaseUpdateTaskResult(
            infobase_name=ib,
            succeeded=False,
        )
        for ib in infobases
    ]


@pytest.fixture()
def mixed_update_result(infobases):
    succeeded = True
    return [
        core_models.InfoBaseUpdateTaskResult(infobase_name=ib, succeeded=(succeeded := not succeeded))
        for ib in infobases
    ]


@pytest.fixture()
def success_aws_result(infobases):
    return [
        core_models.InfoBaseAWSUploadTaskResult(
            infobase_name=ib, succeeded=True, upload_size=random.randint(1000, 1000**2)
        )
        for ib in infobases
    ]


@pytest.fixture()
def failed_aws_result(infobases):
    return [core_models.InfoBaseAWSUploadTaskResult(infobase_name=ib, succeeded=False) for ib in infobases]


@pytest.fixture()
def mixed_aws_result(infobases):
    succeeded = True
    return [
        core_models.InfoBaseAWSUploadTaskResult(
            infobase_name=ib,
            succeeded=(succeeded := not succeeded),
            upload_size=random.randint(1000, 1000**2) if succeeded else 0,
        )
        for ib in infobases
    ]


@pytest.fixture()
def mock_asyncio_subprocess_succeeded(mocker: MockerFixture):
    subprocess_mock = AsyncMock()
    subprocess_mock.returncode = 0
    subprocess_mock.pid = random.randint(1000, 3000)
    return mocker.patch("asyncio.create_subprocess_shell", return_value=subprocess_mock)


@pytest.fixture()
def mock_asyncio_subprocess_failed(mocker: MockerFixture):
    subprocess_mock = AsyncMock()
    subprocess_mock.returncode = -1
    subprocess_mock.pid = random.randint(1000, 3000)
    return mocker.patch("asyncio.create_subprocess_shell", return_value=subprocess_mock)


@pytest.fixture()
def mock_asyncio_subprocess_timeouted(mocker: MockerFixture):
    subprocess_mock = AsyncMock()
    subprocess_mock.returncode = 0
    subprocess_mock.pid = random.randint(1000, 3000)

    async def subprocess_sleep(*args):
        asyncio.sleep(10)

    subprocess_mock.communicate = AsyncMock(side_effect=subprocess_sleep)

    return mocker.patch("asyncio.create_subprocess_shell", return_value=subprocess_mock)


@pytest.fixture()
def mock_asyncio_subprocess_communication_error(mocker: MockerFixture):
    subprocess_mock = AsyncMock()
    subprocess_mock.returncode = 0
    subprocess_mock.pid = random.randint(1000, 3000)

    subprocess_mock.communicate = AsyncMock(side_effect=Exception)

    return mocker.patch("asyncio.create_subprocess_shell", return_value=subprocess_mock)


@pytest.fixture()
def mock_asyncio_subprocess_termination_error(mocker: MockerFixture):
    subprocess_mock = AsyncMock()
    subprocess_mock.returncode = 0
    subprocess_mock.pid = random.randint(1000, 3000)

    subprocess_mock.terminate = AsyncMock(side_effect=Exception)

    return mocker.patch("asyncio.create_subprocess_shell", return_value=subprocess_mock)


@pytest.fixture()
def mock_get_platform_full_path(mocker: MockerFixture):
    return mocker.patch("core.utils.get_platform_full_path", return_value="")


@pytest.fixture()
def mock_cluster_postgres_infobase(mocker: MockerFixture):
    db_server = "test_postgres_db_server"
    db_name = "test_postgres_db_name"
    db_user = "test_postgres_db_user"
    info_base_mock = Mock()
    info_base_mock.return_value.DBMS = POSTGRES_NAME
    info_base_mock.return_value.dbServerName = db_server
    info_base_mock.return_value.dbName = db_name
    info_base_mock.return_value.dbUser = db_user
    cci_mock = mocker.patch("core.cluster.comcntr.ClusterCOMControler")
    cci_mock.return_value.get_info_base = info_base_mock
    return db_server, db_name, db_user


@pytest.fixture()
def mock_cluster_mssql_infobase(mocker: MockerFixture):
    db_server = "test_mssql_db_server"
    db_name = "test_mssql_db_name"
    db_user = "test_mssql_db_user"
    info_base_mock = Mock()
    info_base_mock.return_value.DBMS = "MSSQL"
    info_base_mock.return_value.dbServerName = db_server
    info_base_mock.return_value.dbName = db_name
    info_base_mock.return_value.dbUser = db_user
    cci_mock = mocker.patch("core.cluster.comcntr.ClusterCOMControler")
    cci_mock.return_value.get_info_base = info_base_mock
    return db_server, db_name, db_user


@pytest.fixture()
def mock_prepare_postgres_connection_vars(mocker: MockerFixture):
    return_value = ("test_db_host", "5432", "test_db_pwd")
    mocker.patch("utils.postgres.prepare_postgres_connection_vars", return_value=return_value)
    return return_value


@pytest.fixture()
def mock_configuration_metadata():
    return "БухгалтерияПредприятия", Version("3.0.108.206")


@pytest.fixture()
def mock_configuration_manifest(mocker: MockerFixture):
    content = dedent(
        """Vendor=Фирма "1С"
        Name=БухгалтерияПредприятия
        Version=3.0.111.25
        AppVersion=8.3
        [Config1]
        Catalog=1С:Бухгалтерия предприятия /Бухгалтерия предприятия
        Destination=1C/Accounting
        Source=1Cv8new.dt
        [Config2]
        Catalog=1С:Бухгалтерия предприятия /Бухгалтерия предприятия (демо)
        Destination=1C/DemoAccounting
        Source=1Cv8.dt
    """
    )
    mocker.patch("builtins.open", mock_open(read_data=content))
    return "БухгалтерияПредприятия", Version("3.0.111.25")


@pytest.fixture()
def mock_configuration_manifest_new(mocker: MockerFixture):
    content = dedent(
        """Vendor=Фирма "1С"
        Name=БухгалтерияПредприятия
        Version=3.0.113.17
        AppVersion=8.3
        [Config1]
        Catalog=1С:Бухгалтерия предприятия /Бухгалтерия предприятия
        Destination=1C/Accounting
        Source=1Cv8new.dt
        [Config2]
        Catalog=1С:Бухгалтерия предприятия /Бухгалтерия предприятия (демо)
        Destination=1C/DemoAccounting
        Source=1Cv8.dt
    """
    )
    mocker.patch("builtins.open", mock_open(read_data=content))
    return "БухгалтерияПредприятия", Version("3.0.113.17")


@pytest.fixture()
def mock_configuration_manifest_updinfo(mocker: MockerFixture):
    versions = "3.0.108.206;3.0.109.61;3.0.110.20;3.0.110.24;3.0.110.29;3.0.111.16;3.0.111.20"
    content = dedent(
        f"""Version=3.0.111.25
        FromVersions=;{versions};
        UpdateDate=21.04.2022
    """
    )
    mocker.patch("builtins.open", mock_open(read_data=content))
    return [Version(v) for v in versions.split(";")]


@pytest.fixture()
def mock_configuration_manifest_updinfo_new(mocker: MockerFixture):
    versions = "3.0.110.24;3.0.110.29;3.0.111.16;3.0.111.25;3.0.112.31;3.0.112.34;3.0.113.16"
    content = dedent(
        f"""Version=3.0.113.17
        FromVersions=;{versions};
        UpdateDate=26.05.2022
    """
    )
    mocker.patch("builtins.open", mock_open(read_data=content))
    return [Version(v) for v in versions.split(";")]
