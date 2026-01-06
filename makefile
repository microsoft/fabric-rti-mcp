fmt: format check

format:
	ruff format fabric_rti_mcp

check:
	ruff check fabric_rti_mcp --fix

test:
	pytest

typecheck:
	ty check fabric_rti_mcp

precommit: fmt typecheck test

ci:
	ruff format --check fabric_rti_mcp
	ruff check fabric_rti_mcp
	pytest

run:
	uvx .

live-test:
	python -m tests.live.test_kusto_tools_live