#!/bin/bash
set -e

echo "Running code quality checks..."

echo -e "\nRunning isort..."
isort .

echo -e "\nRunning Black..."
black .

echo -e "\nRunning Flake8..."
flake8 .

echo -e "\nRunning MyPy..."
mypy . --explicit-package-bases 

echo -e "\nAll checks passed successfully!"
