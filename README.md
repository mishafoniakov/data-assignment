# Data Assignment

Проект генерирует синтетические JSONL-логи пайплайна, загружает их в DuckDB
идемпотентно и строит аналитический отчёт по этапам, ошибкам и LLM-вызовам.

## Что внутри

- `generate_logs.py` — генератор синтетических логов.
- `analytics/ingest.py` — загрузка JSONL-логов в DuckDB, пропуск битых строк, идемпотентность.
- `analytics/report.py` — аналитический отчёт по данным из DuckDB.
- `configs/` — настройки пайплайна, SQL-схемы, SQL отчётов и тестовые данные.
- `models/` — Pydantic-модели лог-событий, отчётов и тест-кейсов.
- `tests/` — pytest-проверки парсинга, event id и аналитических метрик.
- `Dockerfile`, `docker-compose.yml` — контейнерный запуск полного пайплайна.
- `run.sh` — единая точка запуска локального или Docker-пайплайна.

## Быстрый старт

Требования:

- Python `3.13`
- `uv`

Полный локальный запуск:

```bash
./run.sh local
```

То же через `make`:

```bash
make run
```

Команда генерирует `sample_logs/app.log`, пересоздаёт локальную `analytics.duckdb`,
дважды запускает ingest для проверки идемпотентности и печатает отчёт.

## Docker

Требования:

- Docker
- Docker Compose v2

Полный запуск в контейнере:

```bash
./run.sh docker
```

Или через `make`:

```bash
make docker-run
```

Отдельные Docker-команды:

```bash
make docker-compose-config
make docker-build
```

В Docker Compose база DuckDB хранится в volume, путь задаётся через `DUCKDB_PATH`.

## Проверки

Полный локальный CI:

```bash
make ci
```

Отдельные проверки:

```bash
make lint
make test
make test-ingest
make test-metrics
```

`make ci` выполняет:

- `uv sync`
- `ruff`
- pytest по каждому файлу тестов
- полный локальный pipeline через `run.sh local`

GitHub Actions дополнительно проверяет Docker Compose, сборку Docker-образа и
полный Docker pipeline.

## Артефакты

Генерируемые файлы не коммитятся:

- `sample_logs/*.log`
- `pipeline.log`
- `analytics.duckdb`
- `*.duckdb.wal`
- cache-папки Python/ruff/pytest

## Полезные команды

```bash
make help
make generate
make ingest
make report
make clean
```
