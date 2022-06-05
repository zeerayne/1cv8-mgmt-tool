.PHONY: test
test:
	poetry run pytest --spec

.PHONY: install
install:
	poetry install --no-root --no-dev
