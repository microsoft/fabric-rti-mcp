fmt:
	isort .
	black .

lint:
	flake8 .
	mypy fabric_rti_mcp --explicit-package-bases

test:
	pytest

precommit: fmt lint test

run:
	uvx .

live-test:
	python -m tests.live.test_kusto_tools_live