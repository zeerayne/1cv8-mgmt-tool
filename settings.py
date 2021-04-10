import logging
from util.debug import is_debug

DEFAULT_DICT_KEY = 'default'

AWS_ENABLED = True
AWS_ACCESS_KEY_ID = 'AKIAJK6QTCLWZRTP7TPA'
AWS_SECRET_ACCESS_KEY = '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'
AWS_REGION_NAME = 'eu-central-1'
AWS_BUCKET_NAME = '24vol-backup'
AWS_RETENTION_DAYS = 3
AWS_THREADS = 8
AWS_RETRIES = 1
AWS_RETRY_PAUSE = 60
AWS_CHUNK_SIZE = 2048*1024*1024  # 2 Gb

EMAIL_NOTIFY_ENABLED = True
EMAIL_SMTP_HOST = 'smtp.timeweb.ru'
EMAIL_SMTP_PORT = 25
EMAIL_LOGIN = 'robot@dpsoft.org'
EMAIL_PASSWORD = 'uvQ2g8Ic'
EMAIL_FROM = 'robot@dpsoft.org'
EMAIL_TO = ['i_bogdanov@dpsoft.org', ]

MSSQL_MAINTENANCE_ENABLED = False
MSSQL_SHRINK_LOG_SIZE = 64
MSSQL_CREDENTIALS = {
    'sa@10.16.42.203': 'Qwerty!23',
    'sa@10.16.42.204': 'Qwerty!23',
}
MSSQL_ALIASES = {
    'localhost': '10.16.42.203'
}

PG_BACKUP_ENABLED = False
PG_BACKUP_PATH = 'E:\\backup\\pgdump'
PG_CREDENTIALS = {
    'postgres@localhost': 'Qwerty!23',
    'postgres@192.168.0.99': 'Qwerty!23',
}
PG_DUMP_PATH = 'D:\\PostgreSQL\\10.3-2.1C\\bin\\pg_dump.exe'
PG_MAINTENANCE_ENABLED = False
PG_VACUUMDB_PATH = 'D:\\PostgreSQL\\10.3-2.1C\\bin\\vacuumdb.exe'

BACKUP_PATH = 'D:\\backup\\dt'
BACKUP_RETENTION_DAYS = 3
BACKUP_REPLICATION_ENABLED = False
# В случае, если используются сетевые диски, пользователь должен быть авторизаван для корректного доступа к ним
# В дальнейшем необходимо использовать win32wnet.WNetAddConnection2(NetResource, Password, UserName, Flags)
BACKUP_REPLICATION_PATHS = ('\\\\10.16.42.205\\share\\backup\\dt',)
# Количество повторных попыток сделать резервную копию при возникновении ошибки
# Если установлено значение 0, повторные попытки предприниматься не будут
BACKUP_RETRIES = 1
BACKUP_THREADS = 2

LOG_PATH = 'D:\\backup\\log'
LOG_RETENTION_DAYS = 60

UPDATE_PATH = 'D:\\v8updates'
UPDATE_THREADS = 1

MAINTENANCE_THREADS = 1

V8_CLUSTER_ADMIN_NAME = 'Администратор'
V8_CLUSTER_ADMIN_PWD = 'Spineworx64'
V8_INFO_BASE_CREDENTIALS = {
    DEFAULT_DICT_KEY: ('Администратор', ''),
    'buh-med': ('backup', ''),  # ('Администратор', '﻿g7y1C1ZRb14H'),
    'buh-24gr': ('backup', ''),  # ('Администратор', 'oZCN9LbasYuU'),
    'buh-best-life': ('backup', ''),  # ('Администратор', '30K146y633zi'),
    'buh-ip-bykov': ('backup', ''),  # ('Администратор', 'I6S4C09Qa03R'),
    'buh-moduz-po-zakonu': ('backup', ''),  # ('Администратор', 'P988Z0I7817v'),
    'buh-dp-izhevsk': ('backup', ''),  # ('Администратор', 'acB077SK60Dq'),
    'buh-dp-plasmonic': ('backup', ''),  # ('Администратор', '93P3110kBhrH'),
    # 'buh-ip-kuznetsov': ('backup', ''),  # ('Администратор', 'U6cgMike44AB'),
    # 'buh-ip-ylianov': ('backup', ''),  # ('Администратор', '0s0bTf3OjHGT'),
    # 'buh-ip-lepenkov': ('backup', ''),  # ('Администратор', 'bWBImw7DhOEf'),
    # 'buh-planeta-sporta': ('backup', ''),  # ('Администратор', '02E7wM39r01f'),
    'zup': ('backup', ''),  # ('Администратор', '83CjNjY3c69z'),
    # 'buh-razvitie': ('backup', ''),  # ('Администратор', 'xjWsARC3BFdy'),
    # 'buh-innkorp': ('backup', ''),  # ('Администратор', '6j1QenUa8XYU'),
    # 'buh-innkorp-nn': ('backup', ''),  # ('Администратор', 'Xn603J6pKq5Z'),
    # 'buh-biznes-tehnologii': ('backup', ''),  # ('Администратор', 'XumzMwA1hmww'),
}
V8_PLATFORM_PATH = 'C:\\Program Files\\1cv8'
V8_SERVER_AGENT = {
    'address': '10.16.42.203',
    'port': '1540',
}
V8_INFO_BASES_EXCLUDE = [
    'com-test',
    'com-test-2',
    'buh-innkorp-legacy',
	'labtrud-lt-np',
	'labtrud-uks',
	'labtrud-ot', 
	'labtrud-lt-cfo',
    'zup-planeta-sporta',
    'buh-ip-kuznetsov',
    'buh-24gr-oskol',
    'labtrud-demo',
    'buh-best-life-copy',
]
# Пауза в секундах между началом блокировки ИБ и принудительным завершением сеансов
V8_LOCK_INFO_BASE_PAUSE = 5
V8_MAINTENANCE_ENABLED = True

logFormatter = logging.Formatter('%(asctime)s [%(levelname)-5.5s]  %(message)s')
rootLogger = logging.getLogger()
rootLogger.setLevel(logging.DEBUG)

fileHandler = logging.FileHandler('{0}/{1}'.format(LOG_PATH, '1cv8-mgmt.log'))
fileHandler.setFormatter(logFormatter)
fileHandler.setLevel(logging.DEBUG)
rootLogger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
consoleHandler.setLevel(logging.DEBUG)
rootLogger.addHandler(consoleHandler)

for logger_name in ['botocore', 'boto3', 'urllib3', 's3transfer']:
    logging.getLogger(logger_name).setLevel(logging.INFO)


def format_path(path):
    if not path.endswith('\\'):
        path += '\\'
    return path


attrs = globals()
for key, value in dict(attrs).items():
    if key in (
            'BACKUP_PATH',
            'LOG_PATH',
            'V8_PLATFORM_PATH',
            'UPDATE_PATH',
            'PG_BACKUP_PATH'
    ):
        attrs[key] = format_path(value)
BACKUP_REPLICATION_PATHS = (format_path(path) for path in BACKUP_REPLICATION_PATHS)

if is_debug():
    from util.debug import DEBUG_MONKEY_PATCH
    with open(DEBUG_MONKEY_PATCH, 'r', encoding='utf-8') as debug_file:
        _locals = {}
        for line in debug_file:
            if 'settings.' in line:
                exec(line.replace('settings.', ''), globals(), _locals)
        for key, value in _locals.items():
            attrs[key] = value
