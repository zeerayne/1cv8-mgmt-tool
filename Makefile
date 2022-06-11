.PHONY: test
test:
	poetry run pytest --spec -W ignore::DeprecationWarning:pytest_freezegun

.PHONY: install
install:
	poetry install --no-root --no-dev
