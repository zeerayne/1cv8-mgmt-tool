import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from typing import List

import core.types as core_types

from conf import settings


def make_message(caption, html_body):
    now = datetime.now()
    msg = MIMEMultipart('alternative')
    msg['Subject'] = '{0} {1}'.format(caption, now.strftime('%d.%m.%Y'))
    msg['From'] = settings.EMAIL_FROM
    msg['To'] = ','.join(settings.EMAIL_TO)

    part = MIMEText(html_body, 'html')
    msg.attach(part)
    return msg


def make_html_table(caption: str, resultset: List[core_types.InfoBaseTaskResultBase]) -> str:
    style = "style='min-width: 100px; text-align: center; border: 1px solid black;'"
    table = "<table><caption style='white-space: nowrap;'>{caption}</caption>{body}</table>"
    table_body = ''
    succeeded = 0
    for task_result in resultset:
        if task_result.succeeded:
            succeeded += 1
        else:
            table_body += f"<tr style='color:#aa0000'><td {style}>{task_result.infobase_name}</td><td {style}>FAILED</td></tr>"
    if succeeded > 0:
        table_body = f"<tr style='color:#00aa00'><td {style}>{succeeded}</td><td {style}>SUCCEEDED</td></tr>" + table_body
    html = table.format(caption=caption, body=table_body)
    return html


def send_notification(caption, html_body):
    with smtplib.SMTP(settings.EMAIL_SMTP_HOST, settings.EMAIL_SMTP_PORT) as server:
        server.login(settings.EMAIL_LOGIN, settings.EMAIL_PASSWORD)
        msg = make_message(caption, html_body)
        server.sendmail(settings.EMAIL_FROM, settings.EMAIL_TO, msg.as_string())