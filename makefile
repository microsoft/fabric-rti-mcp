fmt:
	isort .
	black .

lint:
flake8 .
mypy fabric_rti_mcp --explicit-package-bases 

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

# Docker targets
docker-build:
	docker build -t fabric-rti-mcp .

docker-run:
	docker run -p 8000:8000 \
		-e FABRIC_RTI_TRANSPORT=http \
		-e KUSTO_SERVICE_URI=https://help.kusto.windows.net/ \
		-e KUSTO_SERVICE_DEFAULT_DB=Samples \
		fabric-rti-mcp

# Azure Container Apps deployment targets
deploy:
	chmod +x deploy/deploy.sh
	./deploy/deploy.sh

cleanup:
	chmod +x deploy/cleanup.sh
	./deploy/cleanup.sh

# Show deployment help
deploy-help:
	@echo "Available deployment commands:"
	@echo "  make deploy     - Deploy to Azure Container Apps (interactive)"
	@echo "  make cleanup    - Clean up Azure resources (interactive)"
	@echo "  make docker-build - Build Docker image locally"
	@echo "  make docker-run - Run Docker container locally"
	@echo ""
	@echo "Prerequisites for Azure deployment:"
	@echo "  - Azure CLI installed and logged in (az login)"
	@echo "  - Container Apps extension (installed automatically)"
	@echo ""
	@echo "The deploy command will prompt you for:"
	@echo "  - Resource group name"
	@echo "  - Azure region"
	@echo "  - Container registry name"
	@echo "  - Kusto service configuration"

.PHONY: fmt lint test precommit run docker-build docker-run deploy cleanup deploy-help
