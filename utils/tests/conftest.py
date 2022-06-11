from unittest.mock import MagicMock, Mock

import pytest
from pytest_mock import MockerFixture


@pytest.fixture
def mock_smtp(mocker: MockerFixture):
    return mocker.patch('smtplib.SMTP', return_value=MagicMock())


@pytest.fixture
def mock_smtp_login(mock_smtp):
    smtp_login_mock = Mock()
    type(mock_smtp.return_value.__enter__.return_value).login = smtp_login_mock
    return smtp_login_mock


@pytest.fixture
def mock_smtp_sendmail(mock_smtp):
    smtp_sendmail_mock = Mock()
    type(mock_smtp.return_value.__enter__.return_value).sendmail = smtp_sendmail_mock
    return smtp_sendmail_mock


@pytest.fixture
def mock_email_message(mocker: MockerFixture):
    return mocker.patch('email.mime.multipart.MIMEMultipart.as_string', return_value='test_email_message_string')
