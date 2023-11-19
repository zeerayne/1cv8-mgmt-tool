.PHONY: install
install:
	poetry install --no-root --no-dev

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

.PHONY: code-style
code-style:
	poetry run isort . 
	poetry run black .

.PHONY: flake8
flake8:
	poetry run flake8 .
