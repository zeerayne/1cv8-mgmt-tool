.PHONY: install
install:
	poetry install --no-root --no-dev

.PHONY: install-dev
install-dev:
	poetry install --no-root
	poetry run pre-commit install

.PHONY: test
test:
	poetry run pytest --spec -W ignore::DeprecationWarning:pytest_freezegun

.PHONY: code-style
code-style:
	poetry run isort . && poetry run yapf --recursive --in-place --verbose .
