import pytest
from pytest_mock import MockerFixture

import core.types as core_types

from core.exceptions import SubprocessException, V8Exception
from maintenance import rotate_logs, _maintenance_v8, _maintenance_vacuumdb


@pytest.mark.asyncio
async def test_rotate_logs_calls_inner_func(mocker: MockerFixture, infobase):
    """
    `rotate_logs` calls `remove_old_files_by_pattern` for rotating logs
    """
    remove_old_files_mock = mocker.patch('core.utils.remove_old_files_by_pattern')
    await rotate_logs(infobase)
    remove_old_files_mock.assert_awaited()


@pytest.mark.asyncio
async def test_maintenance_v8_calls_execute_v8_command(mocker: MockerFixture, infobase, mock_get_platform_full_path):
    """
    Maintenance with 1cv8 tools calls execute_v8_command to run created command
    """
    execute_v8_command_mock = mocker.patch('maintenance.execute_v8_command')
    await _maintenance_v8(infobase)
    execute_v8_command_mock.assert_awaited()


@pytest.mark.asyncio
async def test_maintenance_v8_returns_maintenance_result_type_when_succeeded(
    mocker: MockerFixture, infobase, mock_get_platform_full_path
):
    """
    Maintenance with 1cv8 tools returns result of `InfoBaseMaintenanceTaskResult` type if no errors
    """
    execute_v8_command_mock = mocker.patch('maintenance.execute_v8_command')
    result = await _maintenance_v8(infobase)
    assert isinstance(result, core_types.InfoBaseMaintenanceTaskResult)


@pytest.mark.asyncio
async def test_maintenance_v8_returns_maintenance_result_type_when_failed(
    mocker: MockerFixture, infobase, mock_get_platform_full_path
):
    """
    Maintenance with 1cv8 tools returns result of `InfoBaseMaintenanceTaskResult` type if an error occured
    """
    execute_v8_command_mock = mocker.patch('maintenance.execute_v8_command', side_effect=V8Exception)
    result = await _maintenance_v8(infobase)
    assert isinstance(result, core_types.InfoBaseMaintenanceTaskResult)


@pytest.mark.asyncio
async def test_maintenance_v8_returns_success_result_for_exact_infobase(
    mocker: MockerFixture, infobase, mock_get_platform_full_path
):
    """
    Maintenance with 1cv8 tools returns success result for exact infobase which was provided if no errors
    """
    execute_v8_command_mock = mocker.patch('maintenance.execute_v8_command')
    result = await _maintenance_v8(infobase)
    assert result.infobase_name == infobase


@pytest.mark.asyncio
async def test_maintenance_v8_returns_failed_result_for_exact_infobase(
    mocker: MockerFixture, infobase, mock_get_platform_full_path
):
    """
    Maintenance with 1cv8 tools returns failed result for exact infobase which was provided if an error occured
    """
    execute_v8_command_mock = mocker.patch('maintenance.execute_v8_command', side_effect=V8Exception)
    result = await _maintenance_v8(infobase)
    assert result.infobase_name == infobase


@pytest.mark.asyncio
async def test_maintenance_v8_returns_success_result(mocker: MockerFixture, infobase, mock_get_platform_full_path):
    """
    Maintenance with 1cv8 tools returns success result if no errors
    """
    execute_v8_command_mock = mocker.patch('maintenance.execute_v8_command')
    result = await _maintenance_v8(infobase)
    assert result.succeeded == True


@pytest.mark.asyncio
async def test_maintenance_v8_returns_failed_result_if_error(mocker: MockerFixture, infobase, mock_get_platform_full_path):
    """
    Maintenance with 1cv8 tools returns failed result if an error occured
    """
    execute_v8_command_mock = mocker.patch('maintenance.execute_v8_command', side_effect=V8Exception)
    result = await _maintenance_v8(infobase)
    assert result.succeeded == False


@pytest.mark.asyncio
async def test_maintenance_vacuumdb_returns_maintenance_result_type_when_succeeded(
    mocker: MockerFixture, 
    infobase,
    mock_cluster_postgres_infobase,
    mock_prepare_postgres_connection_vars
):
    """
    Maintenance with vacuumdb returns result of `InfoBaseMaintenanceTaskResult` type if no errors
    """
    execute_subprocess_command_mock = mocker.patch('maintenance.execute_subprocess_command')
    result = await _maintenance_vacuumdb(infobase)
    assert isinstance(result, core_types.InfoBaseMaintenanceTaskResult)


@pytest.mark.asyncio
async def test_maintenance_vacuumdb_returns_maintenance_result_type_when_failed(
    mocker: MockerFixture, 
    infobase,
    mock_cluster_postgres_infobase,
    mock_prepare_postgres_connection_vars
):
    """
    Maintenance with vacuumdb returns result of `InfoBaseMaintenanceTaskResult` type if an error occured
    """
    execute_subprocess_command_mock = mocker.patch('maintenance.execute_subprocess_command', side_effect=SubprocessException)
    result = await _maintenance_vacuumdb(infobase)
    assert isinstance(result, core_types.InfoBaseMaintenanceTaskResult)


@pytest.mark.asyncio
async def test_maintenance_vacuumdb_returns_maintenance_result_type_when_no_credentials(
    infobase,
    mock_cluster_postgres_infobase
):
    """
    Maintenance with vacuumdb returns result of `InfoBaseMaintenanceTaskResult` type if no credentials found for db
    """
    result = await _maintenance_vacuumdb(infobase)
    assert isinstance(result, core_types.InfoBaseMaintenanceTaskResult)


@pytest.mark.asyncio
async def test_maintenance_vacuumdb_returns_result_for_exact_infobase_when_succeeded(
    mocker: MockerFixture, 
    infobase,
    mock_cluster_postgres_infobase,
    mock_prepare_postgres_connection_vars
):
    """
    Maintenance with vacuumdb returns result for exact infobase which was provided if no errors
    """
    execute_subprocess_command_mock = mocker.patch('maintenance.execute_subprocess_command')
    result = await _maintenance_vacuumdb(infobase)
    assert result.infobase_name == infobase


@pytest.mark.asyncio
async def test_maintenance_vacuumdb_returns_result_for_exact_infobase_when_failed(
    mocker: MockerFixture, 
    infobase,
    mock_cluster_postgres_infobase,
    mock_prepare_postgres_connection_vars
):
    """
    Maintenance with vacuumdb returns result for exact infobase which was provided if an error occured
    """
    execute_subprocess_command_mock = mocker.patch('maintenance.execute_subprocess_command', side_effect=SubprocessException)
    result = await _maintenance_vacuumdb(infobase)
    assert result.infobase_name == infobase


@pytest.mark.asyncio
async def test_maintenance_vacuumdb_returns_result_for_exact_infobase_when_no_credentials(
    infobase,
    mock_cluster_postgres_infobase
):
    """
    Maintenance with vacuumdb returns result for exact infobase which was provided if no credentials found for db
    """
    result = await _maintenance_vacuumdb(infobase)
    assert result.infobase_name == infobase


@pytest.mark.asyncio
async def test_maintenance_vacuumdb_returns_sucess_result_when_succeeded(
    mocker: MockerFixture, 
    infobase,
    mock_cluster_postgres_infobase,
    mock_prepare_postgres_connection_vars
):
    """
    Maintenance with vacuumdb returns success result if no errors
    """
    execute_subprocess_command_mock = mocker.patch('maintenance.execute_subprocess_command')
    result = await _maintenance_vacuumdb(infobase)
    assert result.succeeded == True


@pytest.mark.asyncio
async def test_maintenance_vacuumdb_returns_failed_result_when_failed(
    mocker: MockerFixture, 
    infobase,
    mock_cluster_postgres_infobase,
    mock_prepare_postgres_connection_vars
):
    """
    Maintenance with vacuumdb returns failed result if an error occured
    """
    execute_subprocess_command_mock = mocker.patch('maintenance.execute_subprocess_command', side_effect=SubprocessException)
    result = await _maintenance_vacuumdb(infobase)
    assert result.succeeded == False


@pytest.mark.asyncio
async def test_maintenance_vacuumdb_returns_failed_result_when_no_credentials(
    infobase,
    mock_cluster_postgres_infobase
):
    """
    Maintenance with vacuumdb returns failed result if no credentials found for db
    """
    result = await _maintenance_vacuumdb(infobase)
    assert result.succeeded == False
