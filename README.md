# Описание

Набор утилит, облегчающих эксплуатацию кластера 1С Предприятие 8. 

Доступные функции:
1. Резервное копирования информационных баз средствами платформы 1С или средствами PostgreSQL
2. Копирование бэкапов в любое S3-совместимое хранилище
3. Ротация бэкапов
4. Ротация логов
5. Ротация журналов регистрации информационных баз
6. Обновление информационных баз

# Установка

Утилиты взаимодействуют с кластером 1С Предприятие при помощи поставляемой в комплекте с платформой 1С Предприятие COM-компоненты, поэтому поддерживаются только ОС Windows

## Установка внешних зависимостей

Для работы необходимы 
- Python 3.7 или более новый 
- [Poetry](https://python-poetry.org/)
- Платформа 1С Предприятие

### Python

#### Установка Python с помощью winget

```powershell
winget install Python.Python.3
```

#### Установка Python с помощью chocolatey

```powershell
choco install python3
```

### poetry

```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

### Регистрация COM-компоненты 1С Предприятие

Регистрировать необходимо COM-компоненту той же версии, что и агент сервера, к которому будет выполнятся подключение

Выполнить команду с правами администратора

```powershell
regsvr32 "C:\Program Files\1cv8\[version]\bin\comcntr.dll" 
```

## Установка зависимостей проекта

```powershell
poetry install --no-root
```

# Настройка

TODO

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
