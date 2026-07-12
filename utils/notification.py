import logging
import requests
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List

import core.models as core_models
from conf import settings

log = logging.getLogger(__name__)


def format_result_as_text(caption: str, resultset: List[core_models.InfoBaseTaskResultBase]) -> str:
    """
    Форматирует результаты задачи в текст с эмодзи для Telegram.
    Пример:
    Backup
    ✅ accounting — SUCCEEDED
    ❌ trade — FAILED
    """
    lines = [caption]
    for task_result in resultset:
        if task_result.succeeded:
            lines.append(f"✅ {task_result.infobase_name} — SUCCEEDED")
        else:
            lines.append(f"❌ {task_result.infobase_name} — FAILED")

    return "\n".join(lines)


def send_telegram_notification(caption: str, text_body: str):
    """
    Отправляет уведомление через Telegram Bot API.
    """
    bot_token = settings.NOTIFY_TELEGRAM_BOT_ID
    chat_id = settings.NOTIFY_TELEGRAM_CHAT_ID

    if not bot_token or not chat_id:
        log.warning("Telegram notification skipped: BOT_ID or CHAT_ID is empty")
        return

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": f"{caption}\n\n{text_body}",
        "parse_mode": "HTML",
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        log.info(f"Telegram notification sent successfully to {chat_id}")
    except requests.RequestException as e:
        log.error(f"Failed to send Telegram notification: {e}")


def make_message(caption, html_body):
    now = datetime.now()
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "{0} {1}".format(caption, now.strftime("%d.%m.%Y"))
    msg["From"] = settings.NOTIFY_EMAIL_FROM
    msg["To"] = ",".join(settings.NOTIFY_EMAIL_TO)

    part = MIMEText(html_body, "html")
    msg.attach(part)
    return msg


def make_html_table(caption: str, resultset: List[core_models.InfoBaseTaskResultBase]) -> str:
    style = "style='min-width: 100px; text-align: center; border: 1px solid black;'"
    table = "<table><caption style='white-space: nowrap;'>{caption}</caption>{body}</table>"
    table_body = ""
    succeeded = 0
    for task_result in resultset:
        if task_result.succeeded:
            succeeded += 1
        else:
            table_body += f"\
            <tr style='color:#aa0000'><td {style}>{task_result.infobase_name}</td><td {style}>FAILED</td></tr>"

    if succeeded > 0:
        table_body = (
            f"\
        <tr style='color:#00aa00'><td {style}>{succeeded}</td><td {style}>SUCCEEDED</td></tr>"
            + table_body
        )
    html = table.format(caption=caption, body=table_body)
    return html


def send_email_notification(caption, html_body):
    with smtplib.SMTP(
        settings.NOTIFY_EMAIL_SMTP_HOST,
        settings.NOTIFY_EMAIL_SMTP_PORT,
        timeout=settings.NOTIFY_EMAIL_CONNECT_TIMEOUT,
    ) as session:
        if settings.NOTIFY_EMAIL_SMTP_SSL_REQUIRED:
            session.starttls()
        session.login(settings.NOTIFY_EMAIL_LOGIN, settings.NOTIFY_EMAIL_PASSWORD)
        msg = make_message(caption, html_body)
        session.sendmail(settings.NOTIFY_EMAIL_FROM, settings.NOTIFY_EMAIL_TO, msg.as_string())
