fmt: format check

format:
	ruff format fabric_rti_mcp

check:
	ruff check fabric_rti_mcp --fix

test:
	pytest

precommit: fmt test

run:
	uvx .

live-test:
	python -m tests.live.test_kusto_tools_live