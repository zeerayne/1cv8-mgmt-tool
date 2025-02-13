![Pytest](https://github.com/zeerayne/1cv8-mgmt-tool/actions/workflows/pytest.yaml/badge.svg) [![Coverage Status](https://coveralls.io/repos/github/zeerayne/1cv8-mgmt-tool/badge.svg?branch=master)](https://coveralls.io/github/zeerayne/1cv8-mgmt-tool?branch=master)

# Описание

Набор утилит, облегчающих эксплуатацию кластера 1С Предприятие 8. 

Доступные функции:
1. Резервное копирование информационных баз средствами платформы 1С или средствами PostgreSQL
2. Копирование бэкапов в любое S3-совместимое хранилище
3. Ротация бэкапов
4. Ротация логов
5. Ротация журналов регистрации информационных баз
6. Обновление конфигураций информационных баз
7. Уведомления на email

В планах:
1. [ ] Резервное копирование конфигурации кластера
2. [ ] Восстановление конфигурации кластера
3. [ ] Уведомления в telegram
4. [x] Возможность работы через утилиту `rac` и сервер администрирования `ras` вместо использования COM-компоненты

# Установка

Утилиты взаимодействуют с кластером 1С Предприятие при помощи поставляемой в комплекте с платформой 1С Предприятие COM-компоненты, поэтому поддерживаются только ОС Windows

## Установка внешних зависимостей

Для работы необходимы 
- Python 3.8 или более новый 
- [Poetry](https://python-poetry.org/)
- [Платформа 1С Предприятие 8.3](https://releases.1c.ru/project/Platform83)

### Python

#### Установка Python с помощью [winget](https://github.com/microsoft/winget-cli)

```powershell
winget install Python.Python.3
```

#### Установка Python с помощью [chocolatey](https://chocolatey.org/)

```powershell
choco install python3
```

#### Установка Python с помощью [scoop](https://scoop.sh/)

```powershell
scoop install python
```

### Poetry

```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

### Регистрация COM-компоненты 1С Предприятие

> [!TIP]
> Регистрация COM-компоненты не требуется, если предполагается работа с кластером через утилиту `rac`

Регистрировать необходимо COM-компоненту той же версии, что и агент сервера, к которому будет выполняться подключение

Выполнить команду с **правами администратора**

```powershell
regsvr32 "C:\Program Files\1cv8\[version]\bin\comcntr.dll"
```

## Установка зависимостей проекта

Клонирование git-репозитория

```powershell
git clone https://github.com/zeerayne/1cv8-mgmt-tool.git
```

Создание виртуального окружения, установка сторонних зависимостей

```powershell
cd 1cv8-mgmt-tool
poetry install --no-root --only main
```

# Настройка

Приложение имеет настройки по умолчанию, которые можно увидеть в модуле `conf.default_settings`. Если в используемом модуле настроек какая-либо настройка отсутствует, будет использовано её значение по умолчанию. Это сделано, чтобы минимизировать размер файла настроек.

## Модуль настроек

Для корректной работы приложению требуется наличие файла с настройками.
Файл настроек по своей сути является модулем python и не может быть размещён вне корневой директории приложения.
По умолчанию импорт настроек осуществляется из файла `settings.py` в корневой директории проекта.

В комплекте с приложением поставляется файл `settings.tpl.py`, который содержит в себе все возможные настройки с примерами значений и служит удобным шаблоном для файла настроек.

Чтобы создать файл настроек, достаточно скопировать шаблон:
```powershell
cp settings.tpl.py settings.py
```

### Изменения имени и местоположения модуля настроек

При необходимости изменять имя и местоположение модуля возможно при помощи переменной окружения `1CV8MGMT_SETTINGS_MODULE`.
Это может быть полезным при работе с несколькими кластерами/несколькими наборами отличающихся настроек.

Примеры:
1. Если задать переменной окружения `1CV8MGMT_SETTINGS_MODULE` значение `settings_1`, то импорт настроек будет осуществляться из файла `.\settings_1.py`
2. `1CV8MGMT_SETTINGS_MODULE="settings.cluster1.backup"` -> `.\settings\cluster1\backup.py`

## Редактирование настроек

Поставляемый в комплекте файл настроек поделён на логические секции для удобства конфигурирования и чтения.

TIP: для работы с путями в шаблонном файле настроек предлагается использовать функцию `os.path.join` т.к. символ `\` в python требует экранирования таким же символом, и конструкции вида `C:\\backup\\1cv8` или `\\\\192.168.1.2\\backup\\1cv8` не очень легко воспринимаются. С использованием функции-хэлпера выглядит немного лучше: `join('C:\\', 'backup', '1cv8')` или `join('\\\\192.168.1.2', 'backup', '1cv8')`. Тем не менее, можно использовать и обычные строки без функции-хэлпера.

### 1CV8 platform

Настройки взаимодействия с платформой 1С Предприятие. Эти настройки необходимы для работы любых частей приложения

> [!CAUTION]
> В режиме взаимодействия с кластером 1С Предприятие через клиент администрирования кластера невозможно выполнять обновление информационных баз.
> На текущий момент обновление ИБ поддерживается только при работе через COM-компоненту

|Параметр|Описание|
|-------:|:-------|
|`V8_CLUSTER_ADMIN_CREDENTIALS`|Учетные данные администратора кластера 1С Предприятие|
|`V8_CLUSTER_CONTROL_MODE`     |Режим взаимодействия с кластером 1С Предприятие: через COM-компоненту (`'com'`) или через клиент администрирования кластера (`'rac'`)|
|`V8_INFOBASES_CREDENTIALS`    |Сопоставление с именами информационных баз, именами пользователей и паролями, которые будут использованы для подключения к информационным базам. Если информационная база не указана в списке в явном виде, для подклчения к ней будут использованы данные от записи `default`|
|`V8_INFOBASES_EXCLUDE`        |Список с именами информационных баз, которые будут пропущены. Никакие операции с ними выполняться не будут|
|`V8_INFOBASES_ONLY`           |Если список не пустой, все действия будут проводиться только с информационными базами, указанными в нём|
|`V8_LOCK_INFO_BASE_PAUSE`     |Пауза в секундах между блокировкой фоновых заданий ИБ и продолжением дальнейших действий. Бывает полезно т.к. некоторые фоновые задания могут долго инициализироваться и создать сеанс уже после установления блокировки|
|`V8_RAS`                      |Параметры подключения к серверу администрирования кластера 1С Предприятие: address и port|
|`V8_SERVER_AGENT`             |Параметры подключения к агенту сервера 1С Предприятие: address и port|
|`V8_PERMISSION_CODE`          |Код блокировки начала новых сеансов, который будет устанавливаться при совершении операций с информационной базой|
|`V8_PLATFORM_PATH`            |Путь к платформе 1С Предприятие. Последняя версия платформы будет определена автоматически|

### Backup

Настройки для настройки резервного копирования информационных баз

|Параметр|Описание|
|-------:|:-------|
|`BACKUP_CONCURRENCY`            |Параллелизм: сколько резервных копий может создаваться одновременно|
|`BACKUP_PATH`                   |Путь к каталогу, куда будут помещены файлы резервных копий|
|`BACKUP_PG`                     |Включает или отключает функцию создания резервных копий средствами PostgreSQL для совместимых информационных баз (базы данных которых размещены на СУБД PostgreSQL), принимает значения `True` или `False`|
|`BACKUP_RETENTION_DAYS`         |Копии старше, чем количество дней в этой настройке будут удалсяться из каталога резервных копий при работе резервного копирования|
|`BACKUP_REPLICATION`            |Включает или отключает функцию копирования резервных копий в дополнительные локации (например на сетевой диск), принимает значения `True` или `False`|
|`BACKUP_REPLICATION_CONCURRENCY`|Параллелизм: сколько резервных копий может копироваться в места репликации одновременно|
|`BACKUP_REPLICATION_PATHS`      |Список путей, куда резервные копии будут реплицированы|
|`BACKUP_RETRIES_V8`             |Количество повторных попыток создания резервной копии средствами 1С Предприятие в случае возникновении ошибки. Если установлено значение 0, повторные попытки предприниматься не будут|
|`BACKUP_RETRIES_PG`             |Количество повторных попыток загрузки резервной копии средствами PostgreSQL (см. секцию PostgreSQL). Если установлено значение 0, повторные попытки предприниматься не будут|
|`BACKUP_TIMEOUT_V8`             |Таймаут в секундах, по истечению которого резервное копирование информационной базы считается неуспешным и принудительно завершается|

### Update

Настройки для настройки обновлений конфигураций информационных баз

|Параметр|Описание|
|-------:|:-------|
|`UPDATE_CONCURRENCY`|Параллелизм: сколько информационных может обновляться одновременно|
|`UPDATE_PATH`       |Путь к каталогу с конфигурациями и обновлениями 1С Предприятия. По умолчанию обновления устанавливаются в каталог `C:\Users\<username>\AppData\Roaming\1C\1cv8\tmplts\`|

### Maintenance

Настройки для обслуживания информационных баз

|Параметр|Описание|
|-------:|:-------|
|`MAINTENANCE_CONCURRENCY`                    |Параллелизм: сколько информационных баз может обслуживаться одновременно|
|`MAINTENANCE_PG`                             |Включает или отключает функцию обслуживания базы данных средствами СУБД PostgreSQL. Если включено, будет выполнено обслуживание утилитой [vacuumdb](https://www.postgresql.org/docs/current/app-vacuumdb.html) для поддерживаемых информационных баз|
|`MAINTENANCE_V8`                             |Включает или отключает функцию обслуживания информационной базы средствами 1С Предприятие. Если включено, будет выполнено удаление старых записей из журнала регистрации информационной базы|
|`MAINTENANCE_LOG_RETENTION_DAYS`             |Лог-файлы, оставляемые процессами резервного копирования, обновления и обсулуживания информационной базы старше, чем количество дней в этой настройке будут удаляться из файловой системы|
|`MAINTENANCE_REGISTRATION_LOG_RETENTION_DAYS`|Записи журнала регистрации старше, чем количество дней в этой настройке будут удаляться из журнала регистрации|
|`MAINTENANCE_TIMEOUT_V8`                     |Таймаут в секундах, по истечению которого обслуживание информационной базы считается неуспешным и принудительно завершается|

### Amazon S3

Содержит настройки, которые управляют загрузкой резервных копий на S3-совместимые хранилища.
Для загрузки резервных копий используется библиотека [`boto`](https://github.com/boto/boto3), иногда знание этого облегчает поиск докумнтации на S3-совместимых сторонних сервисах.

|Параметр|Описание|
|-------:|:-------|
|`AWS_ENABLED`          |Включает или отключает функцию загрузки резервных копий на AWS, принимает значения `True` или `False`. По умолчанию имеет значение `False`|
|`AWS_CONCURRENCY`      |Параллелизм: сколько резервных копий может загружаться на AWS одновременно|
|`AWS_ENDPOINT_URL`     |Опциональный параметр, необходимый если используется не AWS, а другой провайдер. Например для Yandex Object Storage эндпоинт имеет значение `https://storage.yandexcloud.net`. Если используется AWS S3 параметр можно удалить или оставить пустым|
|`AWS_ACCESS_KEY_ID`    |Ключ для программного доступа к AWS. [Инструкция по получению](https://docs.aws.amazon.com/general/latest/gr/aws-sec-cred-types.html#access-keys-and-secret-access-keys), аналогичная инструкция есть у многих S3-совместимых сервисов и хранилищ|
|`AWS_SECRET_ACCESS_KEY`|Секрет для ключа программного доступа, выдаётся вместе с access_key|
|`AWS_BUCKET_NAME`      |Имя бакета, в который будут загружаться резервные копии. [Инструкция по созданию бакета](https://docs.aws.amazon.com/AmazonS3/latest/userguide/create-bucket-overview.html)|
|`AWS_REGION_NAME`      |Опциональный параметр. Регион, в котором размещен бакет|
|`AWS_RETENTION_DAYS`   |Копии старше, чем количество дней в этой настройке будут удалсяться из бакета при работе резервного копирования|
|`AWS_RETRIES`          |Количество повторных попыток загрузки резервной копии в случае возникновении ошибки. Если установлено значение 0, повторные попытки предприниматься не будут. Полезно, если интернет-соединение нестабильно|
|`AWS_RETRY_PAUSE`      |Пауза в секундах перед осуществлением следующей попытки. Бывает полезно, если текущая попытка завершилась неудачей из-за сетевых проблем. Иногда имеет смысл подождать устранения проблем, прежде чем предпринимать повторные попытки|

### PostgreSQL

Настройки для работы с информационными базами средствами СУБД PostgreSQL (см. секции Backup и Maintenance)

|Параметр|Описание|
|-------:|:-------|
|`PG_CREDENTIALS`   |Сопоставление, содержащее имена пользователей СУБД PostgreSQL в формате user@host и пароли к ним. Резервное копирование базы данных средствами PostgreSQL осуществляется от имени того же пользователя и хоста СУБД, который указан в метаданных информационной базы в кластере 1С Предприятия|
|`PG_BIN_PATH`      |Как правило, это путь к каталогу `bin` от PostgreSQL, из которого будут использоваться утилиты для резервного копирования (`pg_dump.exe`) и обслуживания (`vacuumdb.exe`) баз данных. Версия утилит не обязательно должна соответствовать версии сервера СУБД. Опционально можно скопировать необходимые утилиты и их зависимости в другой каталог, и использовать его|

### Notifications

При окончании резервного копирования и загрузки копий на AWS приложение может отправить нотификаицию с результатами на email.
Это самый простой способ следить за работой приложения ~~не привлекая внимания санитаров~~ не имея системы мониторинга/алертинга.

|Параметр|Описание|
|-------:|:-------|
|`NOTIFY_EMAIL_ENABLED`          |Включает или отключает функцию отправки писем с уведомлениями, принимает значения `True` или `False`|
|`NOTIFY_EMAIL_CAPTION`          |Тема письма. К теме так же будет добавлена дата отправки|
|`NOTIFY_EMAIL_CONNECT_TIMEOUT`  |Таймаут соединения с почтовым сервером в секундах|
|`NOTIFY_EMAIL_SMTP_HOST`        |SMTP-хост для отправки писем, например `smtp.gmail.com`|
|`NOTIFY_EMAIL_SMTP_PORT`        |Порт SMTP, может отличаться в зависимости от хоста|
|`NOTIFY_EMAIL_SMTP_SSL_REQUIRED`|Требуется ли обязательное шифрование на SMTP-хосте, принимает значения `True` или `False`|
|`NOTIFY_EMAIL_LOGIN`            |Логин (как правило совпадает с адресом почтового ящика) для авторизации на SMTP-хосте|
|`NOTIFY_EMAIL_PASSWORD`         |Пароль для авторизации на SMTP-хосте|
|`NOTIFY_EMAIL_FROM`             |Email, который будет указан в поле `from` письма|
|`NOTIFY_EMAIL_TO`               |Список имейлов, на которые будет отправлено письмо. Например `['email1@corp.mail', 'email2@gmail.com']`|

### Logging

Настройки, определяющие куда записывать логи от работы приложения и используемых внешних утилит

|Параметр|Описание|
|-------:|:-------|
|`LOG_FILENAME`|Имя файла, в который будет записываться лог работы приложения|
|`LOG_LEVEL`   |Уровень логирования. Выше уровень - меньше сообщений в логе. Доступные значения по возрастанию: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`|
|`LOG_PATH`    |Путь, куда будут сохраняться все логи как самого приложения, так и используемых внешних утилит|

# Использование

## Запуск резервного копирования

```powershell
poetry run python backup.py
```

## Запуск обслуживания

```powershell
poetry run python maintenance.py
```

## Запуск обновления

```powershell
poetry run python update.py
```

## Запуск любого сценария с кастомным модулем настроек

```powershell
$env:1CV8MGMT_SETTINGS_MODULE = 'custom_settings.py'; poetry run python <scenario>.py
```
