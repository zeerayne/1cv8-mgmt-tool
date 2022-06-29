.PHONY: install
install:
	poetry install --no-root --no-dev

.PHONY: install-dev
install-dev:
	poetry install --no-root

.PHONY: test
test:
	poetry run pytest --spec -W ignore::DeprecationWarning:pytest_freezegun
