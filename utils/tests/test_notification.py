from xml.etree import ElementTree

from conf import settings
from utils.notification import make_html_table, make_message, send_notification


def test_html_table_empty_input():
    """
    HTML table for empty results should contain no `<tr>` elements
    """
    result = make_html_table('', [])
    assert '<tr' not in result


def test_html_table_caption_is_set():
    """
    HTML table caption is contained in output
    """
    caption = 'test_caption'
    result = make_html_table(caption, [])
    assert 'test_caption' in result


def test_html_table_all_succeeded(success_base_result):
    """
    HTML table for all succeeded results should contain only `SUCCEEDED` block
    """
    result = make_html_table('', success_base_result)
    assert 'SUCCEEDED' in result
    assert 'FAILED' not in result


def test_html_table_all_failed(failed_base_result):
    """
    HTML table for all failed results should contain only `FAILED` block
    """
    result = make_html_table('', failed_base_result)
    assert 'FAILED' in result
    assert 'SUCCEEDED' not in result


def test_html_table_mixed(mixed_base_result):
    """
    HTML table for mixed results should contain both `SUCCEEDED` and `FAILED` blocks
    """
    result = make_html_table('', mixed_base_result)
    assert 'FAILED' in result
    assert 'SUCCEEDED' in result


def test_html_table_all_succeeded_output_is_valid_xml(success_base_result):
    """
    HTML table for all succeeded results should generate valid XML tree
    """
    result = make_html_table('', success_base_result)
    assert ElementTree.fromstring(result)


def test_html_table_all_failed_output_is_valid_xml(failed_base_result):
    """
    HTML table for all failed results should generate valid XML tree
    """
    result = make_html_table('', failed_base_result)
    assert ElementTree.fromstring(result)


def test_html_table_mixed_output_is_valid_xml(mixed_base_result):
    """
    HTML table for mixed results should generate valid XML tree
    """
    result = make_html_table('', mixed_base_result)
    assert ElementTree.fromstring(result)


def test_send_notification_calls_smtp(mock_smtp, mock_smtp_login, mock_smtp_sendmail):
    """
    To send email, SMTP should be created with proper SMTP host and port
    """
    send_notification('', '')
    mock_smtp.assert_called_with(settings.NOTIFY_EMAIL_SMTP_HOST, settings.NOTIFY_EMAIL_SMTP_PORT)


def test_send_notification_calls_smtp_login(mock_smtp, mock_smtp_login, mock_smtp_sendmail):
    """
    To send email, should be logged in on smtp server
    """
    send_notification('', '')
    mock_smtp_login.assert_called_with(settings.NOTIFY_EMAIL_LOGIN, settings.NOTIFY_EMAIL_PASSWORD)


def test_send_notification_calls_smtp_sendmail(mock_smtp, mock_smtp_login, mock_smtp_sendmail, mock_email_message):
    """
    To send email, should actually send message
    """
    send_notification('', '')
    mock_smtp_sendmail.assert_called_with(settings.NOTIFY_EMAIL_FROM, settings.NOTIFY_EMAIL_TO, mock_email_message())


def test_make_message_includes_content():
    """
    Email message should include content
    """
    content = 'test_content'
    result = make_message('', content)
    assert content in result.as_string()


def test_make_message_includes_caption():
    """
    Email message should include caption
    """
    caption = 'test_caption'
    result = make_message(caption, '')
    assert caption in result.as_string()
