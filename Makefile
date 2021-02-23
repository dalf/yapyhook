install:
	"$PIP" install -U "pip >= 20.2" setuptools wheel
	"$PIP" install --use-feature="2020-resolver" -r "$REQUIREMENTS"

qa:
	flake8 yapyhook tests
	python -m pytest tests -vv  --cov-report html --cov=yapyhook

lint:
	autoflake --in-place --recursive yapyhook tests
	isort --project=yapyhook yapyhook tests
	black --target-version=py36 yapyhook tests

check:
	black --check --diff --target-version=py36 yapyhook tests
	flake8 yapyhook tests
	isort --check --diff --project=yapyhook yapyhook tests
	mypy yapyhook tests
