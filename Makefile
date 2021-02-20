qa:
	flake8 hooks tests
	python -m pytest tests -vv  --cov-report html --cov=hooks

lint:
	autoflake --in-place --recursive hooks tests
	isort --project=hooks hooks tests
	black --target-version=py36 hooks tests

check:
	black --check --diff --target-version=py36 hooks tests
	flake8 hooks tests
	mypy hooks tests
	isort --check --diff --project=hooks hooks tests
