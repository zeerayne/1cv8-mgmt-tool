import logging
import os

AWS_RETRY_PAUSE = 600

DATE_FORMAT = '%Y-%m-%d'
DATETIME_FORMAT = '%Y-%m-%d-%H-%M-%S'

FILENAME_SEPARATOR = '_'

V8_CLUSTER_ADMIN_CREDENTIALS = ('Администратор', '')
V8_INFO_BASES_CREDENTIALS = {
    'default': ('Администратор', ''),
}
V8_INFO_BASES_EXCLUDE = []
# Пауза в секундах между началом блокировки ИБ и принудительным завершением сеансов
V8_LOCK_INFO_BASE_PAUSE = 5
V8_PLATFORM_PATH = os.path.join('C:\\', 'Program Files', '1cv8')
V8_SERVER_AGENT = {
    'address': 'localhost',
    'port': '1540',
}

log_format = '%(asctime)s [%(levelname)-3.3s] %(message)s'
logFormatter = logging.Formatter(log_format)
rootLogger = logging.getLogger()
rootLogger.setLevel(logging.DEBUG)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
consoleHandler.setLevel(logging.DEBUG)
rootLogger.addHandler(consoleHandler)

for logger_name in ['aioboto3', 'aiobotocore', 'botocore', 'boto3', 'urllib3']:
    logging.getLogger(logger_name).setLevel(logging.INFO)
