import logging
import os

AWS_ENABLED = False
AWS_CONCURRENCY = 3
AWS_ENDPOINT_URL = ''
AWS_ACCESS_KEY_ID = ''
AWS_SECRET_ACCESS_KEY = ''
AWS_REGION_NAME = ''
AWS_BUCKET_NAME = ''
AWS_RETENTION_DAYS = 90
AWS_RETRIES = 2

EMAIL_NOTIFY_ENABLED = False
EMAIL_SMTP_HOST = ''
EMAIL_SMTP_PORT = 25
EMAIL_LOGIN = ''
EMAIL_PASSWORD = ''
EMAIL_FROM = ''
EMAIL_TO = ['', ]

PG_BACKUP_ENABLED = False
PG_CREDENTIALS = {
    'postgres@localhost': '',
}
PG_BIN_PATH = os.path.join('C:\\', 'Program Files', 'PostgreSQL', '14.2-1.1C', 'bin')
PG_DUMP_PATH = os.path.join(PG_BIN_PATH, 'pg_dump.exe')
PG_VACUUMDB_PATH = os.path.join(PG_BIN_PATH, 'vacuumdb.exe')

BACKUP_CONCURRENCY = 3
BACKUP_PATH = os.path.join('C:\\', 'backup', '1cv8')
BACKUP_RETENTION_DAYS = 30
BACKUP_REPLICATION_ENABLED = False
# В случае, если используются сетевые диски, пользователь должен быть авторизаван для корректного доступа к ним
# В дальнейшем необходимо использовать win32wnet.WNetAddConnection2(NetResource, Password, UserName, Flags)
BACKUP_REPLICATION_PATHS = (os.path.join('\\\\192.168.1.2', 'backup', '1cv8'), )
# Количество повторных попыток сделать резервную копию при возникновении ошибки
# Если установлено значение 0, повторные попытки предприниматься не будут
BACKUP_RETRIES = 1

LOG_PATH = os.path.join('C:\\', 'log', '1cv8')
LOG_RETENTION_DAYS = 60

UPDATE_PATH = os.path.join('C:\\', 'v8updates')
UPDATE_CONCURRENCY = 3

MAINTENANCE_CONCURRENCY = 3
MAINTENANCE_PG = False
MAINTENANCE_V8 = False
MAINTENANCE_REGISTRATION_LOG_RETENTION_DAYS = 90

V8_CLUSTER_ADMIN_CREDENTIALS = ('Администратор', '')
V8_INFO_BASES_CREDENTIALS = {
    'default': ('Администратор', ''),
}
V8_SERVER_AGENT = {
    'address': 'localhost',
    'port': '1540',
}
V8_PLATFORM_PATH = os.path.join('C:\\', 'Program Files', '1cv8')

log_format = '%(asctime)s [%(levelname)-3.3s] %(message)s'
logFormatter = logging.Formatter(log_format)
rootLogger = logging.getLogger()
rootLogger.setLevel(logging.DEBUG)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
consoleHandler.setLevel(logging.DEBUG)
rootLogger.addHandler(consoleHandler)

fileHandler = logging.FileHandler(os.path.join(LOG_PATH, '1cv8-mgmt-tool.log'))
fileHandler.setFormatter(logging.getLogger().handlers[0].format)
fileHandler.setLevel(logging.DEBUG)
rootLogger.addHandler(fileHandler)

for logger_name in ['aioboto3', 'aiobotocore', 'botocore', 'boto3', 'urllib3']:
    logging.getLogger(logger_name).setLevel(logging.INFO)
