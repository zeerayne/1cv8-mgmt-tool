import os
import random

import pytest

from core import types as core_types


random.seed(0)


def pytest_generate_tests(metafunc):
    os.environ['PYTHONPATH'] = '.'
    os.environ['1CV8MGMT_SETTINGS_MODULE'] = 'tests.settings'


@pytest.fixture
def infobases():
    return ['infobase_test_01', 'infobase_test_02', 'infobase_test_03']


@pytest.fixture
def infobase(infobases):
    return infobases[0]


@pytest.fixture
def success_base_result(infobases):
    return [core_types.InfoBaseTaskResultBase(
        infobase_name=ib,
        succeeded=True,
    ) for ib in infobases]


@pytest.fixture
def failed_base_result(infobases):
    return [core_types.InfoBaseTaskResultBase(
        infobase_name=ib,
        succeeded=False,
    ) for ib in infobases]


@pytest.fixture
def mixed_base_result(infobases):
    succeeded = True
    return [core_types.InfoBaseTaskResultBase(
        infobase_name=ib,
        succeeded=(succeeded := not succeeded),
    ) for ib in infobases]


@pytest.fixture
def success_backup_result(infobases):
    return [core_types.InfoBaseBackupTaskResult(
        infobase_name=ib,
        succeeded=True,
        backup_filename=f'./{ib}.testbackup'
    ) for ib in infobases]


@pytest.fixture
def failed_backup_result(infobases):
    return [core_types.InfoBaseBackupTaskResult(
        infobase_name=ib,
        succeeded=False,
    ) for ib in infobases]


@pytest.fixture
def mixed_backup_result(infobases):
    succeeded = True
    return [core_types.InfoBaseBackupTaskResult(
        infobase_name=ib,
        succeeded=(succeeded := not succeeded),
        backup_filename=f'./{ib}.testbackup' if succeeded else ''
    ) for ib in infobases]


@pytest.fixture
def success_maintenance_result(infobases):
    return [core_types.InfoBaseMaintenanceTaskResult(
        infobase_name=ib,
        succeeded=True
    ) for ib in infobases]


@pytest.fixture
def failed_maintenance_result(infobases):
    return [core_types.InfoBaseMaintenanceTaskResult(
        infobase_name=ib,
        succeeded=False,
    ) for ib in infobases]


@pytest.fixture
def mixed_maintenance_result(infobases):
    succeeded = True
    return [core_types.InfoBaseMaintenanceTaskResult(
        infobase_name=ib,
        succeeded=(succeeded := not succeeded)
    ) for ib in infobases]


@pytest.fixture
def success_update_result(infobases):
    return [core_types.InfoBaseUpdateTaskResult(
        infobase_name=ib,
        succeeded=True
    ) for ib in infobases]


@pytest.fixture
def failed_update_result(infobases):
    return [core_types.InfoBaseUpdateTaskResult(
        infobase_name=ib,
        succeeded=False,
    ) for ib in infobases]


@pytest.fixture
def mixed_update_result(infobases):
    succeeded = True
    return [core_types.InfoBaseUpdateTaskResult(
        infobase_name=ib,
        succeeded=(succeeded := not succeeded)
    ) for ib in infobases]   


@pytest.fixture
def success_aws_result(infobases):
    return [core_types.InfoBaseAWSUploadTaskResult(
        infobase_name=ib,
        succeeded=True,
        upload_size=random.randint(1000, 1000 ** 2)
    ) for ib in infobases]


@pytest.fixture
def failed_aws_result(infobases):
    return [core_types.InfoBaseAWSUploadTaskResult(
        infobase_name=ib,
        succeeded=False
    ) for ib in infobases]


@pytest.fixture
def mixed_aws_result(infobases):
    succeeded = True
    return [core_types.InfoBaseAWSUploadTaskResult(
        infobase_name=ib,
        succeeded=(succeeded := not succeeded),
        upload_size=random.randint(1000, 1000 ** 2) if succeeded else 0
    ) for ib in infobases]
