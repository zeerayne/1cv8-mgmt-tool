from pytest_mock import MockerFixture

from utils.log import configure_logging


def test_configure_logging_not_raising_exception(mocker: MockerFixture):
    """
    Logging configured without errors
    """
    mocker.patch("logging.getLogger")
    mocker.patch("logging.FileHandler")
    mocker.patch("logging.StreamHandler")
    configure_logging(0)
