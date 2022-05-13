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

## Установка внешних зависимостей

Для работы необходимы 
- Python 3.7 или более новый 
- [Poetry](https://python-poetry.org/)

### Установка Python

#### Установка Python с помощью winget

```powershell
winget install Python.Python.3
```

#### Установка Python с помощью chocolatey

```powershell
choco install python3
```

### Установка poetry

```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
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
