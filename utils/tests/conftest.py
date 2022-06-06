import pytest
from pytest_mock import MockerFixture


@pytest.fixture
def mock_smtp(mocker: MockerFixture):
    return mocker.patch('smtplib.SMTP.connect', return_value=(220, ''))


@pytest.fixture
def mock_smtp_login(mocker: MockerFixture):
    return mocker.patch('smtplib.SMTP.login', return_value=None)


@pytest.fixture
def mock_smtp_sendmail(mocker: MockerFixture):
    return mocker.patch('smtplib.SMTP.sendmail', return_value=None)


@pytest.fixture
def mock_smtp_quit(mocker: MockerFixture):
    return mocker.patch('smtplib.SMTP.quit', return_value=None)


@pytest.fixture
def mock_email_message(mocker: MockerFixture):
    return mocker.patch('email.mime.multipart.MIMEMultipart.as_string', return_value='test_email_message_string')
