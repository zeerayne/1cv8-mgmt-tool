.PHONY: install
install:
	uv sync --frozen --no-group dev --no-group debug

.PHONY: install-dev
install-dev:
	uv sync --frozen --all-groups
	uv run pre-commit install

.PHONY: test
test:
	uv run pytest --spec

.PHONY: test-coverage
test-coverage:
	uv run coverage run -m pytest

.PHONY: ruff
ruff:
	uv run ruff check

.PHONY: format
format:
	uv run ruff check --fix
	uv run ruff format
