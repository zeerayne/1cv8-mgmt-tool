import smtplib
import settings
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def make_message(caption, html_body):
    from datetime import datetime
    now = datetime.now()
    msg = MIMEMultipart('alternative')
    msg['Subject'] = '{0} {1}'.format(caption, now.strftime('%d.%m.%Y'))
    msg['From'] = settings.EMAIL_FROM
    msg['To'] = ','.join(settings.EMAIL_TO)

    part = MIMEText(html_body, 'html')
    msg.attach(part)
    return msg


def make_html_table(caption, result):
    style = """style='min-width: 100px; text-align: center; border: 1px solid black;'"""
    table = """<table><caption style="white-space: nowrap;">{caption}</caption>{body}</table>"""
    table_body = ''
    succeeded = 0
    for e in result:
        if e[1]:
            succeeded += 1
        else:
            table_body += """<tr style='color:#aa0000'><td {style}>{first_column}</td><td {style}>FAILED</td></tr>"""\
                .format(first_column=e[0], style=style)
    if succeeded > 0:
        table_body = """<tr style='color:#00aa00'><td {style}>{first_column}</td><td {style}>SUCCEEDED</td></tr>"""\
                         .format(first_column=succeeded, style=style) + table_body
    result = table.format(caption=caption, body=table_body)
    return result


def send_notification(caption, html_body):
    server = smtplib.SMTP(
        settings.EMAIL_SMTP_HOST,
        settings.EMAIL_SMTP_PORT
    )
    server.login(
        settings.EMAIL_LOGIN,
        settings.EMAIL_PASSWORD
    )
    msg = make_message(caption, html_body)
    server.sendmail(
        settings.EMAIL_FROM,
        settings.EMAIL_TO,
        msg.as_string()
    )
    server.quit()
