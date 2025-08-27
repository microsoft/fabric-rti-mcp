fmt:
	isort .
	black .

lint:
	flake8 .
	mypy . --explicit-package-bases 

test:
	pytest

precommit:
	isort .
	black .
	flake8 .
	mypy . --explicit-package-bases
	pytest

run:
	uvx .

live-test:
	python -m tests.live.test_kusto_tools_live