from os.path import expanduser, join

## ------------- ##
## 1CV8 platform ##
## ------------- ##

V8_CLUSTER_ADMIN_CREDENTIALS = ("Администратор", "")
V8_INFOBASES_CREDENTIALS = {
    "default": ("Администратор", ""),
}
V8_INFOBASES_EXCLUDE = []
V8_INFOBASES_ONLY = []
V8_LOCK_INFO_BASE_PAUSE = 5
V8_SERVER_AGENT = {
    "address": "localhost",
    "port": "1540",
}
V8_PERMISSION_CODE = "0000"
V8_PLATFORM_PATH = join("C:\\", "Program Files", "1cv8")

## ------ ##
## Backup ##
## ------ ##

BACKUP_CONCURRENCY = 3
BACKUP_PATH = join(".", "backup")
BACKUP_PG = False
BACKUP_RETENTION_DAYS = 30
BACKUP_REPLICATION = False
BACKUP_REPLICATION_PATHS = [
    join("\\\\192.168.1.2", "backup", "1cv8"),
]
BACKUP_RETRIES_V8 = 1
BACKUP_RETRIES_PG = 1

## ------ ##
## Update ##
## ------ ##

UPDATE_CONCURRENCY = 3
UPDATE_PATH = join(expanduser("~"), "AppData", "Roaming", "1C", "1cv8", "tmplts")

## ----------- ##
## Maintenance ##
## ----------- ##

MAINTENANCE_CONCURRENCY = 3
MAINTENANCE_PG = False
MAINTENANCE_V8 = False
MAINTENANCE_LOG_RETENTION_DAYS = 60
MAINTENANCE_REGISTRATION_LOG_RETENTION_DAYS = 90

## ---------- ##
## Amazon S3  ##
## ---------- ##

AWS_ENABLED = False
AWS_CONCURRENCY = 9
AWS_ENDPOINT_URL = ""
AWS_ACCESS_KEY_ID = ""
AWS_SECRET_ACCESS_KEY = ""
AWS_REGION_NAME = ""
AWS_BUCKET_NAME = ""
AWS_RETENTION_DAYS = 90
AWS_RETRIES = 1
AWS_RETRY_PAUSE = 600

## ---------- ##
## PostgreSQL ##
## ---------- ##

PG_CREDENTIALS = {
    "postgres@localhost": "",
}
PG_BIN_PATH = join("C:\\", "Program Files", "PostgreSQL", "bin")

## ------------- ##
## Notifications ##
## ------------- ##

NOTIFY_EMAIL_ENABLED = False
NOTIFY_EMAIL_CAPTION = "1cv8-mgmt backup"
NOTIFY_EMAIL_CONNECT_TIMEOUT = 10
NOTIFY_EMAIL_SMTP_HOST = ""
NOTIFY_EMAIL_SMTP_PORT = 25
NOTIFY_EMAIL_SMTP_SSL_REQUIRED = False
NOTIFY_EMAIL_LOGIN = ""
NOTIFY_EMAIL_PASSWORD = ""
NOTIFY_EMAIL_FROM = ""
NOTIFY_EMAIL_TO = [
    "",
]

## ------- ##
## Logging ##
## ------- ##

LOG_FILENAME = "1cv8-mgmt-tool.log"
LOG_LEVEL = "DEBUG"
LOG_PATH = join(".", "log")
