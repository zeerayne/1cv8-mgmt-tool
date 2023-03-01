from unittest.mock import AsyncMock

import pytest

try:
    import pywintypes
except ImportError:
    from surrogate import surrogate

    surrogate("pywintypes").prepare()
    import pywintypes

    pywintypes.com_error = Exception

from core import models as core_models
from core.cluster.comcntr import ClusterCOMControler
from core.cluster.rac import ClusterRACControler
from core.cluster.utils import com_func_wrapper, get_cluster_controller_class
from core.exceptions import V8Exception


@pytest.mark.asyncio()
async def test_com_func_wrapper_awaits_inner_func(infobase):
    """
    `com_func_wrapper` awaits inner coroutine
    """
    coroutine_mock = AsyncMock(side_effect=lambda ib_name: core_models.InfoBaseTaskResultBase(ib_name, True))
    await com_func_wrapper(coroutine_mock, infobase)
    coroutine_mock.assert_awaited()


@pytest.mark.asyncio()
async def test_com_func_wrapper_returns_value_of_inner_func(infobase):
    """
    `com_func_wrapper` returns value from inner coroutine
    """
    coroutine_mock = AsyncMock(side_effect=lambda ib_name: core_models.InfoBaseTaskResultBase(ib_name, True))
    result = await com_func_wrapper(coroutine_mock, infobase)
    assert result.infobase_name == infobase
    assert result.succeeded is True


@pytest.mark.asyncio()
async def test_com_func_wrapper_handle_com_error(infobase, mock_connect_agent, mock_connect_working_process):
    """
    `com_func_wrapper` returns value when com error raised
    """

    def raise_com_error(*args):
        raise pywintypes.com_error

    coroutine_mock = AsyncMock(side_effect=raise_com_error)
    result = await com_func_wrapper(coroutine_mock, infobase)
    assert result.infobase_name == infobase
    assert result.succeeded is False


@pytest.mark.asyncio()
async def test_com_func_wrapper_handle_v8_exception(infobase, mock_connect_agent, mock_connect_working_process):
    """
    `com_func_wrapper` returns value when V8Exception raised
    """

    def raise_v8_exception(*args):
        raise V8Exception

    coroutine_mock = AsyncMock(side_effect=raise_v8_exception)
    result = await com_func_wrapper(coroutine_mock, infobase)
    assert result.infobase_name == infobase
    assert result.succeeded is False
