from os.path import expanduser, join

## ------------- ##
## 1CV8 platform ##
## ------------- ##

V8_CLUSTER_ADMIN_CREDENTIALS = ("Администратор", "cluster_admin_password")
V8_CLUSTER_CONTROL_MODE = "com"
V8_INFOBASES_CREDENTIALS = {
    "default": ("Администратор", "infobase_user_password"),
    "accounting": ("БухАдминистратор", "infobase_user_password"),
    "trade": ("УТАдминистратор", "infobase_user_password"),
}
V8_INFOBASES_EXCLUDE = ["accounting_for_tests", "trade_copy"]
V8_INFOBASES_ONLY = ["accounting_production", "trade_production"]
V8_RAS = {
    "address": "localhost",
    "port": "1545",
}
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
BACKUP_REPLICATION_CONCURRENCY = 3
BACKUP_REPLICATION_PATHS = [
    join("\\\\192.168.1.2", "backup", "1cv8"),
]
BACKUP_RETRIES_V8 = 1
BACKUP_RETRIES_PG = 1
BACKUP_TIMEOUT_V8 = 1200

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
MAINTENANCE_TIMEOUT_V8 = 600

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

## ---------- ##
## PostgreSQL ##
## ---------- ##

PG_CREDENTIALS = {
    "postgres@localhost": "postgres_user_password",
    "usr_1cv8@192.168.1.2:5433": "postgres_user_password",
}
PG_BIN_PATH = join("C:\\", "Program Files", "PostgreSQL", "14.2-1.1C", "bin")

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
