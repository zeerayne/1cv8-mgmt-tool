import os

AWS_ENDPOINT_URL = ''
AWS_REGION_NAME = ''
AWS_RETRY_PAUSE = 600

DATE_FORMAT_1CV8 = '%Y-%m-%d'
DATETIME_FORMAT = '%Y-%m-%d-%H-%M-%S'

EMAIL_CAPTION = '1cv8-mgmt backup'

FILENAME_SEPARATOR = '_'

V8_CLUSTER_ADMIN_CREDENTIALS = ('Администратор', '')
V8_INFO_BASES_CREDENTIALS = {
    'default': ('Администратор', ''),
}
V8_INFO_BASES_EXCLUDE = []
# Пауза в секундах между началом блокировки ИБ и принудительным завершением сеансов
V8_LOCK_INFO_BASE_PAUSE = 5
V8_PERMISSION_CODE = "0000"
V8_PLATFORM_PATH = os.path.join('C:\\', 'Program Files', '1cv8')
V8_SERVER_AGENT = {
    'address': 'localhost',
    'port': '1540',
}
