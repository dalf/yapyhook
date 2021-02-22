qa:
	flake8 yapihook tests
	python -m pytest tests -vv  --cov-report html --cov=yapihook

lint:
	autoflake --in-place --recursive yapihook tests
	isort --project=yapihook yapihook tests
	black --target-version=py36 yapihook tests

check:
	black --check --diff --target-version=py36 yapihook tests
	flake8 yapihook tests
	mypy yapihook tests
	isort --check --diff --project=yapihook yapihook tests
