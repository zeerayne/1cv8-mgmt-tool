import asyncio
from datetime import datetime, timedelta
from unittest.mock import PropertyMock

import pytest
from pytest_mock import MockerFixture

import core.types as core_types
from core.exceptions import SubprocessException, V8Exception
from maintenance import _maintenance_v8, _maintenance_vacuumdb, analyze_results, maintenance_info_base, rotate_logs


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
    mock_prepare_postgres_connection_vars
):
    """
    Maintenance with vacuumdb returns result of `InfoBaseMaintenanceTaskResult` type if no errors
    """
    execute_subprocess_command_mock = mocker.patch('maintenance.execute_subprocess_command')
    result = await _maintenance_vacuumdb(infobase, '', '', '')
    assert isinstance(result, core_types.InfoBaseMaintenanceTaskResult)


@pytest.mark.asyncio
async def test_maintenance_vacuumdb_returns_maintenance_result_type_when_failed(
    mocker: MockerFixture, 
    infobase,
    mock_prepare_postgres_connection_vars
):
    """
    Maintenance with vacuumdb returns result of `InfoBaseMaintenanceTaskResult` type if an error occured
    """
    execute_subprocess_command_mock = mocker.patch('maintenance.execute_subprocess_command', side_effect=SubprocessException)
    result = await _maintenance_vacuumdb(infobase, '', '', '')
    assert isinstance(result, core_types.InfoBaseMaintenanceTaskResult)


@pytest.mark.asyncio
async def test_maintenance_vacuumdb_returns_maintenance_result_type_when_no_credentials(
    infobase
):
    """
    Maintenance with vacuumdb returns result of `InfoBaseMaintenanceTaskResult` type if no credentials found for db
    """
    result = await _maintenance_vacuumdb(infobase, '', '', '')
    assert isinstance(result, core_types.InfoBaseMaintenanceTaskResult)


@pytest.mark.asyncio
async def test_maintenance_vacuumdb_returns_result_for_exact_infobase_when_succeeded(
    mocker: MockerFixture, 
    infobase,
    mock_prepare_postgres_connection_vars
):
    """
    Maintenance with vacuumdb returns result for exact infobase which was provided if no errors
    """
    execute_subprocess_command_mock = mocker.patch('maintenance.execute_subprocess_command')
    result = await _maintenance_vacuumdb(infobase, '', '', '')
    assert result.infobase_name == infobase


@pytest.mark.asyncio
async def test_maintenance_vacuumdb_returns_result_for_exact_infobase_when_failed(
    mocker: MockerFixture, 
    infobase,
    mock_prepare_postgres_connection_vars
):
    """
    Maintenance with vacuumdb returns result for exact infobase which was provided if an error occured
    """
    execute_subprocess_command_mock = mocker.patch('maintenance.execute_subprocess_command', side_effect=SubprocessException)
    result = await _maintenance_vacuumdb(infobase, '', '', '')
    assert result.infobase_name == infobase


@pytest.mark.asyncio
async def test_maintenance_vacuumdb_returns_result_for_exact_infobase_when_no_credentials(
    infobase
):
    """
    Maintenance with vacuumdb returns result for exact infobase which was provided if no credentials found for db
    """
    result = await _maintenance_vacuumdb(infobase, '', '', '')
    assert result.infobase_name == infobase


@pytest.mark.asyncio
async def test_maintenance_vacuumdb_returns_sucess_result_when_succeeded(
    mocker: MockerFixture, 
    infobase,
    mock_prepare_postgres_connection_vars
):
    """
    Maintenance with vacuumdb returns success result if no errors
    """
    execute_subprocess_command_mock = mocker.patch('maintenance.execute_subprocess_command')
    result = await _maintenance_vacuumdb(infobase, '', '', '')
    assert result.succeeded == True


@pytest.mark.asyncio
async def test_maintenance_vacuumdb_returns_failed_result_when_failed(
    mocker: MockerFixture, 
    infobase,
    mock_prepare_postgres_connection_vars
):
    """
    Maintenance with vacuumdb returns failed result if an error occured
    """
    execute_subprocess_command_mock = mocker.patch('maintenance.execute_subprocess_command', side_effect=SubprocessException)
    result = await _maintenance_vacuumdb(infobase, '', '', '')
    assert result.succeeded == False


@pytest.mark.asyncio
async def test_maintenance_vacuumdb_returns_failed_result_when_no_credentials(
    infobase
):
    """
    Maintenance with vacuumdb returns failed result if no credentials found for db
    """
    result = await _maintenance_vacuumdb(infobase, '', '', '')
    assert result.succeeded == False


@pytest.mark.asyncio
async def test_maintenance_info_base_returns_maintenance_result_type_when_succeeded(
    mocker: MockerFixture, 
    infobase,
    mock_cluster_postgres_infobase
):
    """
    Maitenance infobase function returns result of `InfoBaseMaintenanceTaskResult` if succeeded with default settings
    """
    return_value = core_types.InfoBaseMaintenanceTaskResult(infobase, True)
    mocker.patch('maintenance.rotate_logs', return_value=return_value)
    result = await maintenance_info_base(infobase, asyncio.Semaphore(1))
    assert isinstance(result, core_types.InfoBaseMaintenanceTaskResult)


@pytest.mark.asyncio
async def test_maintenance_info_base_returns_maintenance_result_type_when_succeeded_with_v8(
    mocker: MockerFixture, 
    infobase,
    mock_cluster_postgres_infobase
):
    """
    Maitenance infobase function returns result of `InfoBaseMaintenanceTaskResult` if succeeded with MAINTENANCE_V8 == True
    """
    return_value = core_types.InfoBaseMaintenanceTaskResult(infobase, True)
    mocker.patch('conf.settings.MAINTENANCE_V8', new_callable=PropertyMock(return_value=True))
    mocker.patch('core.utils.com_func_wrapper', return_value=return_value)
    mocker.patch('maintenance.rotate_logs', return_value=return_value)
    result = await maintenance_info_base(infobase, asyncio.Semaphore(1))
    assert isinstance(result, core_types.InfoBaseMaintenanceTaskResult)


@pytest.mark.asyncio
async def test_maintenance_info_base_returns_maintenance_result_type_when_succeeded_with_pg(
    mocker: MockerFixture, 
    infobase,
    mock_cluster_postgres_infobase
):
    """
    Maitenance infobase function returns result of `InfoBaseMaintenanceTaskResult` if succeeded with MAINTENANCE_PG == True
    """
    return_value = core_types.InfoBaseMaintenanceTaskResult(infobase, True)
    mocker.patch('conf.settings.MAINTENANCE_PG', new_callable=PropertyMock(return_value=True))
    mocker.patch('maintenance._maintenance_vacuumdb', return_value=return_value)
    mocker.patch('maintenance.rotate_logs', return_value=return_value)
    result = await maintenance_info_base(infobase, asyncio.Semaphore(1))
    assert isinstance(result, core_types.InfoBaseMaintenanceTaskResult)


@pytest.mark.asyncio
async def test_maintenance_info_base_returns_maintenance_result_type_when_succeeded_with_v8_and_pg(
    mocker: MockerFixture, 
    infobase,
    mock_cluster_postgres_infobase
):
    """
    Maitenance infobase function returns result of `InfoBaseMaintenanceTaskResult` 
    if succeeded with MAINTENANCE_V8 == True and MAINTENANCE_PG == True
    """
    return_value = core_types.InfoBaseMaintenanceTaskResult(infobase, True)
    mocker.patch('conf.settings.MAINTENANCE_V8', new_callable=PropertyMock(return_value=True))
    mocker.patch('conf.settings.MAINTENANCE_PG', new_callable=PropertyMock(return_value=True))
    mocker.patch('core.utils.com_func_wrapper', return_value=return_value)
    mocker.patch('maintenance._maintenance_vacuumdb', return_value=return_value)
    mocker.patch('maintenance.rotate_logs', return_value=return_value)
    result = await maintenance_info_base(infobase, asyncio.Semaphore(1))
    assert isinstance(result, core_types.InfoBaseMaintenanceTaskResult)


@pytest.mark.asyncio
async def test_maintenance_info_base_returns_maintenance_result_type_when_failed(
    mocker: MockerFixture, 
    infobase,
    mock_cluster_postgres_infobase
):
    """
    Maitenance infobase function returns result of `InfoBaseMaintenanceTaskResult` if failed with default settings
    """
    return_value = core_types.InfoBaseMaintenanceTaskResult(infobase, False)
    mocker.patch('maintenance.rotate_logs', return_value=return_value)
    result = await maintenance_info_base(infobase, asyncio.Semaphore(1))
    assert isinstance(result, core_types.InfoBaseMaintenanceTaskResult)


@pytest.mark.asyncio
async def test_maintenance_info_base_returns_maintenance_result_type_when_failed_with_v8(
    mocker: MockerFixture, 
    infobase,
    mock_cluster_postgres_infobase
):
    """
    Maitenance infobase function returns result of `InfoBaseMaintenanceTaskResult` if failed with MAINTENANCE_V8 == True
    """
    return_value = core_types.InfoBaseMaintenanceTaskResult(infobase, False)
    mocker.patch('conf.settings.MAINTENANCE_V8', new_callable=PropertyMock(return_value=True))
    mocker.patch('core.utils.com_func_wrapper', return_value=return_value)
    mocker.patch('maintenance.rotate_logs', return_value=return_value)
    result = await maintenance_info_base(infobase, asyncio.Semaphore(1))
    assert isinstance(result, core_types.InfoBaseMaintenanceTaskResult)


@pytest.mark.asyncio
async def test_maintenance_info_base_returns_maintenance_result_type_when_failed_with_pg(
    mocker: MockerFixture, 
    infobase,
    mock_cluster_postgres_infobase
):
    """
    Maitenance infobase function returns result of `InfoBaseMaintenanceTaskResult` if failed with MAINTENANCE_PG == True
    """
    return_value = core_types.InfoBaseMaintenanceTaskResult(infobase, False)
    mocker.patch('conf.settings.MAINTENANCE_PG', new_callable=PropertyMock(return_value=True))
    mocker.patch('maintenance._maintenance_vacuumdb', return_value=return_value)
    mocker.patch('maintenance.rotate_logs', return_value=return_value)
    result = await maintenance_info_base(infobase, asyncio.Semaphore(1))
    assert isinstance(result, core_types.InfoBaseMaintenanceTaskResult)


@pytest.mark.asyncio
async def test_maintenance_info_base_returns_maintenance_result_type_when_failed_with_v8_and_pg(
    mocker: MockerFixture, 
    infobase,
    mock_cluster_postgres_infobase
):
    """
    Maitenance infobase function returns result of `InfoBaseMaintenanceTaskResult` 
    if failed with MAINTENANCE_V8 == True and MAINTENANCE_PG == True
    """
    return_value = core_types.InfoBaseMaintenanceTaskResult(infobase, False)
    mocker.patch('conf.settings.MAINTENANCE_V8', new_callable=PropertyMock(return_value=True))
    mocker.patch('conf.settings.MAINTENANCE_PG', new_callable=PropertyMock(return_value=True))
    mocker.patch('core.utils.com_func_wrapper', return_value=return_value)
    mocker.patch('maintenance._maintenance_vacuumdb', return_value=return_value)
    mocker.patch('maintenance.rotate_logs', return_value=return_value)
    result = await maintenance_info_base(infobase, asyncio.Semaphore(1))
    assert isinstance(result, core_types.InfoBaseMaintenanceTaskResult)


@pytest.mark.asyncio
async def test_maintenance_info_base_returns_maintenance_result_succeeded_when_succeeded(
    mocker: MockerFixture, 
    infobase,
    mock_cluster_postgres_infobase
):
    """
    Maitenance infobase function returns object with succeeded == True if succeeded with default settings
    """
    return_value = core_types.InfoBaseMaintenanceTaskResult(infobase, True)
    mocker.patch('maintenance.rotate_logs', return_value=return_value)
    result = await maintenance_info_base(infobase, asyncio.Semaphore(1))
    assert result.succeeded == True


@pytest.mark.asyncio
async def test_maintenance_info_base_returns_maintenance_result_succeeded_when_succeeded_with_v8(
    mocker: MockerFixture, 
    infobase,
    mock_cluster_postgres_infobase
):
    """
    Maitenance infobase function returns object with succeeded == True if succeeded with MAINTENANCE_V8 == True
    """
    return_value = core_types.InfoBaseMaintenanceTaskResult(infobase, True)
    mocker.patch('conf.settings.MAINTENANCE_V8', new_callable=PropertyMock(return_value=True))
    mocker.patch('core.utils.com_func_wrapper', return_value=return_value)
    mocker.patch('maintenance.rotate_logs', return_value=return_value)
    result = await maintenance_info_base(infobase, asyncio.Semaphore(1))
    assert result.succeeded == True


@pytest.mark.asyncio
async def test_maintenance_info_base_returns_maintenance_result_succeeded_when_succeeded_with_pg(
    mocker: MockerFixture, 
    infobase,
    mock_cluster_postgres_infobase
):
    """
    Maitenance infobase function returns object with succeeded == True if succeeded with MAINTENANCE_PG == True
    """
    return_value = core_types.InfoBaseMaintenanceTaskResult(infobase, True)
    mocker.patch('conf.settings.MAINTENANCE_PG', new_callable=PropertyMock(return_value=True))
    mocker.patch('maintenance._maintenance_vacuumdb', return_value=return_value)
    mocker.patch('maintenance.rotate_logs', return_value=return_value)
    result = await maintenance_info_base(infobase, asyncio.Semaphore(1))
    assert result.succeeded == True


@pytest.mark.asyncio
async def test_maintenance_info_base_returns_maintenance_result_succeeded_when_succeeded_with_v8_and_pg(
    mocker: MockerFixture, 
    infobase,
    mock_cluster_postgres_infobase
):
    """
    Maitenance infobase function returns object with succeeded == True if succeeded with MAINTENANCE_V8 == True and MAINTENANCE_PG == True
    """
    return_value = core_types.InfoBaseMaintenanceTaskResult(infobase, True)
    mocker.patch('conf.settings.MAINTENANCE_V8', new_callable=PropertyMock(return_value=True))
    mocker.patch('conf.settings.MAINTENANCE_PG', new_callable=PropertyMock(return_value=True))
    mocker.patch('core.utils.com_func_wrapper', return_value=return_value)
    mocker.patch('maintenance._maintenance_vacuumdb', return_value=return_value)
    mocker.patch('maintenance.rotate_logs', return_value=return_value)
    result = await maintenance_info_base(infobase, asyncio.Semaphore(1))
    assert result.succeeded == True


@pytest.mark.asyncio
async def test_maintenance_info_base_returns_maintenance_result_failed_when_failed(
    mocker: MockerFixture, 
    infobase,
    mock_cluster_postgres_infobase
):
    """
    Maitenance infobase function returns object with succeeded == False if failed with default settings
    """
    return_value = core_types.InfoBaseMaintenanceTaskResult(infobase, False)
    mocker.patch('maintenance.rotate_logs', return_value=return_value)
    result = await maintenance_info_base(infobase, asyncio.Semaphore(1))
    assert result.succeeded == False


@pytest.mark.asyncio
async def test_maintenance_info_base_returns_maintenance_result_failed_when_failed_with_v8(
    mocker: MockerFixture, 
    infobase,
    mock_cluster_postgres_infobase
):
    """
    Maitenance infobase function returns object with succeeded == False if failed with MAINTENANCE_V8 == True
    """
    return_value = core_types.InfoBaseMaintenanceTaskResult(infobase, False)
    mocker.patch('conf.settings.MAINTENANCE_V8', new_callable=PropertyMock(return_value=True))
    mocker.patch('core.utils.com_func_wrapper', return_value=return_value)
    mocker.patch('maintenance.rotate_logs', return_value=return_value)
    result = await maintenance_info_base(infobase, asyncio.Semaphore(1))
    assert result.succeeded == False


@pytest.mark.asyncio
async def test_maintenance_info_base_returns_maintenance_result_failed_when_failed_with_pg(
    mocker: MockerFixture, 
    infobase,
    mock_cluster_postgres_infobase
):
    """
    Maitenance infobase function returns object with succeeded == False if failed with MAINTENANCE_PG == True
    """
    return_value = core_types.InfoBaseMaintenanceTaskResult(infobase, False)
    mocker.patch('conf.settings.MAINTENANCE_PG', new_callable=PropertyMock(return_value=True))
    mocker.patch('maintenance._maintenance_vacuumdb', return_value=return_value)
    mocker.patch('maintenance.rotate_logs', return_value=return_value)
    result = await maintenance_info_base(infobase, asyncio.Semaphore(1))
    assert result.succeeded == False


@pytest.mark.asyncio
async def test_maintenance_info_base_returns_maintenance_result_failed_when_failed_with_v8_and_pg(
    mocker: MockerFixture, 
    infobase,
    mock_cluster_postgres_infobase
):
    """
    Maitenance infobase function returns object with succeeded == False if failed with MAINTENANCE_V8 == True and MAINTENANCE_PG == True
    """
    return_value = core_types.InfoBaseMaintenanceTaskResult(infobase, False)
    mocker.patch('conf.settings.MAINTENANCE_V8', new_callable=PropertyMock(return_value=True))
    mocker.patch('conf.settings.MAINTENANCE_PG', new_callable=PropertyMock(return_value=True))
    mocker.patch('core.utils.com_func_wrapper', return_value=return_value)
    mocker.patch('maintenance._maintenance_vacuumdb', return_value=return_value)
    mocker.patch('maintenance.rotate_logs', return_value=return_value)
    result = await maintenance_info_base(infobase, asyncio.Semaphore(1))
    assert result.succeeded == False


@pytest.mark.asyncio
async def test_maintenance_info_base_returns_maintenance_result_type_when_rotate_logs_raises_error(
    mocker: MockerFixture, 
    infobase,
    mock_cluster_postgres_infobase
):
    """
    Maitenance infobase function returns result of `InfoBaseMaintenanceTaskResult` type if an error occured in `rotate_logs` function
    """
    mocker.patch('maintenance.rotate_logs', side_effect=Exception)
    result = await maintenance_info_base(infobase, asyncio.Semaphore(1))
    assert isinstance(result, core_types.InfoBaseMaintenanceTaskResult)


@pytest.mark.asyncio
async def test_maintenance_info_base_returns_maintenance_result_type_when_v8_raises_error(
    mocker: MockerFixture, 
    infobase,
    mock_cluster_postgres_infobase
):
    """
    Maitenance infobase function returns result of `InfoBaseMaintenanceTaskResult` type if an error occured in v8 maintenance function with MAINTENANCE_V8 == True
    """
    mocker.patch('conf.settings.MAINTENANCE_V8', new_callable=PropertyMock(return_value=True))
    mocker.patch('core.utils.com_func_wrapper', side_effect=Exception)
    result = await maintenance_info_base(infobase, asyncio.Semaphore(1))
    assert isinstance(result, core_types.InfoBaseMaintenanceTaskResult)


@pytest.mark.asyncio
async def test_maintenance_info_base_returns_maintenance_result_type_when_pg_raises_error(
    mocker: MockerFixture, 
    infobase,
    mock_cluster_postgres_infobase
):
    """
    Maitenance infobase function returns result of `InfoBaseMaintenanceTaskResult` type if an error occured in pg maintenance function with MAINTENANCE_PG == True
    """
    mocker.patch('conf.settings.MAINTENANCE_PG', new_callable=PropertyMock(return_value=True))
    mocker.patch('maintenance._maintenance_vacuumdb', side_effect=Exception)
    result = await maintenance_info_base(infobase, asyncio.Semaphore(1))
    assert isinstance(result, core_types.InfoBaseMaintenanceTaskResult)


@pytest.mark.asyncio
async def test_maintenance_info_base_returns_maintenance_result_failed_when_rotate_logs_raises_error(
    mocker: MockerFixture, 
    infobase,
    mock_cluster_postgres_infobase
):
    """
    Maitenance infobase function returns object with succeeded == False if an error occured in `rotate_logs` function
    """
    mocker.patch('maintenance.rotate_logs', side_effect=Exception)
    result = await maintenance_info_base(infobase, asyncio.Semaphore(1))
    assert result.succeeded == False


@pytest.mark.asyncio
async def test_maintenance_info_base_returns_maintenance_result_failed_when_v8_raises_error(
    mocker: MockerFixture, 
    infobase,
    mock_cluster_postgres_infobase
):
    """
    Maitenance infobase function returns object with succeeded == False if an error occured in v8 maintenance function with MAINTENANCE_V8 == True
    """
    mocker.patch('conf.settings.MAINTENANCE_V8', new_callable=PropertyMock(return_value=True))
    mocker.patch('core.utils.com_func_wrapper', side_effect=Exception)
    result = await maintenance_info_base(infobase, asyncio.Semaphore(1))
    assert result.succeeded == False


@pytest.mark.asyncio
async def test_maintenance_info_base_returns_maintenance_result_failed_when_pg_raises_error(
    mocker: MockerFixture, 
    infobase,
    mock_cluster_postgres_infobase
):
    """
    Maitenance infobase function returns object with succeeded == False if an error occured in pg maintenance function with MAINTENANCE_PG == True
    """
    mocker.patch('conf.settings.MAINTENANCE_PG', new_callable=PropertyMock(return_value=True))
    mocker.patch('maintenance._maintenance_vacuumdb', side_effect=Exception)
    result = await maintenance_info_base(infobase, asyncio.Semaphore(1))
    assert result.succeeded == False


@pytest.mark.asyncio
async def test_maintenance_info_base_calls_rotate_logs_by_default(
    mocker: MockerFixture, 
    infobase,
    mock_cluster_postgres_infobase
):
    """
    Maitenance infobase function calls `rotate_logs` by default
    """
    rotate_logs_mock = mocker.patch('maintenance.rotate_logs')
    await maintenance_info_base(infobase, asyncio.Semaphore(1))
    rotate_logs_mock.assert_awaited_with(infobase)


@pytest.mark.asyncio
async def test_maintenance_info_base_calls_maintenance_v8_with_v8_enabled(
    mocker: MockerFixture, 
    infobase,
    mock_cluster_postgres_infobase
):
    """
    Maitenance infobase function calls `_maintenance_v8` with MAINTENANCE_V8 == True
    """
    return_value = core_types.InfoBaseMaintenanceTaskResult(infobase, False)
    mocker.patch('conf.settings.MAINTENANCE_V8', new_callable=PropertyMock(return_value=True))
    mocker.patch('maintenance.rotate_logs')
    com_func_wrapper_mock = mocker.patch('core.utils.com_func_wrapper', return_value=return_value)
    await maintenance_info_base(infobase, asyncio.Semaphore(1))
    com_func_wrapper_mock.assert_awaited_with(_maintenance_v8, infobase)


@pytest.mark.asyncio
async def test_maintenance_info_base_calls_maintenance_pg_with_pg_enabled(
    mocker: MockerFixture, 
    infobase,
    mock_cluster_postgres_infobase
):
    """
    Maitenance infobase function calls `_maintenance_pg` with MAINTENANCE_PG == True
    """
    return_value = core_types.InfoBaseMaintenanceTaskResult(infobase, False)
    mocker.patch('conf.settings.MAINTENANCE_PG', new_callable=PropertyMock(return_value=True))
    mocker.patch('maintenance.rotate_logs')
    maintenance_vacuumdb_mock = mocker.patch('maintenance._maintenance_vacuumdb', return_value=return_value)
    await maintenance_info_base(infobase, asyncio.Semaphore(1))
    maintenance_vacuumdb_mock.assert_awaited()


def test_analyze_results_calls_inner_func(mocker: MockerFixture, infobases, mixed_maintenance_result):
    start = datetime.now()
    end = start + timedelta(minutes=5)
    analyze_maintenance_result_mock = mocker.patch('maintenance.analyze_maintenance_result')
    analyze_results(infobases, mixed_maintenance_result, start, end)
    analyze_maintenance_result_mock.assert_called_with(mixed_maintenance_result, infobases, start, end)
