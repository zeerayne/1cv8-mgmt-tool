.PHONY: install
install:
	poetry install --no-root --only main

.PHONY: install-dev
install-dev:
	poetry install --no-root
	poetry run pre-commit install

.PHONY: test
test:
	poetry run pytest --spec

.PHONY: test-coverage
test-coverage:
	poetry run coverage run -m pytest

.PHONY: ruff
ruff:
	poetry run ruff check

.PHONY: format
format:
	poetry run ruff check --fix
	poetry run ruff format
