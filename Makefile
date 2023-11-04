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

.PHONY: test-coverage
test-coverage:
	poetry run coverage run -m pytest -W ignore::DeprecationWarning:pytest_freezegun

.PHONY: code-style
code-style:
	poetry run isort . && poetry run black .

.PHONY: flake8
flake8:
	poetry run flake8 .
