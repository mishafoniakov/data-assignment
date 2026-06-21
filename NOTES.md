# NOTES

Заполни по ходу работы — это часть оценки.

## Что сделано
- Добавлен генератор синтетических JSONL-логов `generate_logs.py`.
- Реализован инкрементальный загрузчик `analytics.ingest` в DuckDB.
- Добавлена идемпотентность: повторная загрузка того же файла не создаёт дубликаты.
- Битые строки в логах пропускаются и учитываются в статистике загрузки.
- Бизнес-настройки и SQL-схемы вынесены в корневой пакет `configs/`.
- Структура лог-событий валидируется через Pydantic-модель из корневого пакета `models/`.
- Добавлены аналитические DuckDB view для длительностей этапов, ошибок и LLM-вызовов.
- Добавлен `analytics.report` для вывода агрегированных метрик из DuckDB.
- Настроены локальные команды в `Makefile` и GitHub Actions CI: lint, генерация логов, ingest, повторный ingest и report.
- Добавлены `Dockerfile` и `docker-compose.yml` для запуска полного пайплайна в контейнере.
- Добавлены Docker-цели в `Makefile`: `docker-build`, `docker-compose-config`, `docker-run`.
- Добавлен `run.sh` как единая точка запуска локального и Docker-пайплайна.
- Написан `README.md` с описанием структуры проекта, быстрым стартом, Docker-командами и проверками.

## Решения и допущения
- DuckDB выбран как простой локальный аналитический слой без отдельного сервера.
- Идемпотентность сделана на двух уровнях: хеш файла в `ingestion_log` и стабильный `event_id` на основе `sha256`.
- Для `event_id` используются поля события, которые отличают основные типы логов друг от друга.
- Pydantic используется для нормализации типов и отбраковки некорректных JSON-событий.
- SQL и параметры отчёта вынесены в `configs/report.py`, строки отчёта валидируются Pydantic-моделями из `models/report.py`.
- Тестовые данные ingest вынесены в `configs/ingest_test_data.py`, тест-кейсы описаны Pydantic-моделями из `models/ingest_test_case.py`.
- Тестовые данные метрик вынесены в `configs/metrics_test_data.py`, ожидаемые метрики описаны Pydantic-моделями из `models/metrics_test_case.py`.
- Путь к DuckDB можно переопределить через `DUCKDB_PATH`; это используется в Docker Compose для хранения базы в volume.
- `run.sh local` отвечает за runtime-сценарий, а `make ci` добавляет к нему lint и pytest.
- `run.sh docker` валидирует compose, собирает образ и запускает полный контейнерный пайплайн.
- Сгенерированные артефакты (`*.log`, `*.duckdb`) не коммитятся.

## Что не успел / сделал бы дальше
- Расширить pytest-покрытие на генератор и полную загрузку в DuckDB.
- Добавить CLI-аргумент для пути к DuckDB-базе.
- Добавить отчёты или экспорт агрегатов поверх созданных view.

## Как проверял
- `make ci`
- `./run.sh local`
- `./run.sh docker`
- `uv run ruff check analytics/ configs/ models/ tests/ generate_logs.py`
- `uv run pytest`
- `uv run python generate_logs.py --tasks 200 --out sample_logs/app.log`
- `uv run python -m analytics.ingest sample_logs`
- Повторный запуск `uv run python -m analytics.ingest sample_logs` для проверки идемпотентности.
- `uv run python -m analytics.report`
- `docker compose config`
- `docker build -t data-assignment:latest .`
- `docker compose --profile full run --rm all`
- `make docker-build`
- `make docker-compose-config`
- `make docker-run`
