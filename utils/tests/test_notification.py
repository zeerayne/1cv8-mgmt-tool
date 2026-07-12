from unittest.mock import MagicMock
from xml.etree import ElementTree

from conf import settings
from utils.notification import (
    format_result_as_text,
    make_html_table,
    make_message,
    send_email_notification,
    send_telegram_notification,
)


def test_html_table_empty_input():
    """
    HTML table for empty results should contain no `<tr>` elements
    """
    result = make_html_table("", [])
    assert "<tr" not in result


def test_html_table_caption_is_set():
    """
    HTML table caption is contained in output
    """
    caption = "test_caption"
    result = make_html_table(caption, [])
    assert "test_caption" in result


def test_html_table_all_succeeded(success_base_result):
    """
    HTML table for all succeeded results should contain only `SUCCEEDED` block
    """
    result = make_html_table("", success_base_result)
    assert "SUCCEEDED" in result
    assert "FAILED" not in result


def test_html_table_all_failed(failed_base_result):
    """
    HTML table for all failed results should contain only `FAILED` block
    """
    result = make_html_table("", failed_base_result)
    assert "FAILED" in result
    assert "SUCCEEDED" not in result


def test_html_table_mixed(mixed_base_result):
    """
    HTML table for mixed results should contain both `SUCCEEDED` and `FAILED` blocks
    """
    result = make_html_table("", mixed_base_result)
    assert "FAILED" in result
    assert "SUCCEEDED" in result


def test_html_table_all_succeeded_output_is_valid_xml(success_base_result):
    """
    HTML table for all succeeded results should generate valid XML tree
    """
    result = make_html_table("", success_base_result)
    assert ElementTree.fromstring(result) is not None


def test_html_table_all_failed_output_is_valid_xml(failed_base_result):
    """
    HTML table for all failed results should generate valid XML tree
    """
    result = make_html_table("", failed_base_result)
    assert ElementTree.fromstring(result) is not None


def test_html_table_mixed_output_is_valid_xml(mixed_base_result):
    """
    HTML table for mixed results should generate valid XML tree
    """
    result = make_html_table("", mixed_base_result)
    assert ElementTree.fromstring(result) is not None


def test_send_email_notification_calls_smtp(mock_smtp, mock_smtp_login, mock_smtp_sendmail):
    """
    To send email, SMTP should be created with proper SMTP host, port and timeout
    """
    send_email_notification("", "")
    mock_smtp.assert_called_with(
        settings.NOTIFY_EMAIL_SMTP_HOST,
        settings.NOTIFY_EMAIL_SMTP_PORT,
        timeout=settings.NOTIFY_EMAIL_CONNECT_TIMEOUT,
    )


def test_send_email_notification_calls_smtp_login(mock_smtp, mock_smtp_login, mock_smtp_sendmail):
    """
    To send email, should be logged in on smtp server
    """
    send_email_notification("", "")
    mock_smtp_login.assert_called_with(settings.NOTIFY_EMAIL_LOGIN, settings.NOTIFY_EMAIL_PASSWORD)


def test_send_email_notification_calls_smtp_sendmail(
    mock_smtp, mock_smtp_login, mock_smtp_sendmail, mock_email_message
):
    """
    To send email, should actually send message
    """
    send_email_notification("", "")
    mock_smtp_sendmail.assert_called_with(settings.NOTIFY_EMAIL_FROM, settings.NOTIFY_EMAIL_TO, mock_email_message())


def test_make_message_includes_content():
    """
    Email message should include content
    """
    content = "test_content"
    result = make_message("", content)
    assert content in result.as_string()


def test_make_message_includes_caption():
    """
    Email message should include caption
    """
    caption = "test_caption"
    result = make_message(caption, "")
    assert caption in result.as_string()


def test_format_result_as_text_outputs_emoji_lines(success_base_result):
    """
    Telegram text formatting should include success emoji and infobase names.
    """
    text = format_result_as_text("Backup", success_base_result)
    assert "Backup" in text
    assert "✅" in text
    assert "FAILED" not in text


def test_format_result_as_text_outputs_failed_lines(failed_base_result):
    """
    Telegram text formatting should include failed emoji for failed results.
    """
    text = format_result_as_text("Backup", failed_base_result)
    assert "Backup" in text
    assert "❌" in text
    assert "SUCCEEDED" not in text


def test_send_telegram_notification_calls_requests_post(monkeypatch):
    """
    Telegram notification should call Telegram Bot API with correct payload.
    """
    mock_post = MagicMock()
    mock_response = MagicMock()
    mock_post.return_value = mock_response
    mock_response.raise_for_status = MagicMock()
    monkeypatch.setattr(
        "utils.notification.requests.post",
        mock_post,
    )
    monkeypatch.setattr(settings, "NOTIFY_TELEGRAM_BOT_ID", "test-token")
    monkeypatch.setattr(settings, "NOTIFY_TELEGRAM_CHAT_ID", "12345")

    send_telegram_notification("Caption", "Test message")

    mock_post.assert_called_once_with(
        "https://api.telegram.org/bottest-token/sendMessage",
        json={"chat_id": "12345", "text": "Caption\n\nTest message", "parse_mode": "HTML"},
        timeout=30,
    )


def test_send_telegram_notification_skips_when_missing_credentials(monkeypatch, caplog):
    """
    Telegram notification should be skipped when bot token or chat ID is missing.
    """
    monkeypatch.setattr(settings, "NOTIFY_TELEGRAM_BOT_ID", "")
    monkeypatch.setattr(settings, "NOTIFY_TELEGRAM_CHAT_ID", "")

    send_telegram_notification("Caption", "Test message")

    assert "Telegram notification skipped" in caplog.text
