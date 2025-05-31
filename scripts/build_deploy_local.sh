#!/bin/bash

# Check if version was provided as argument
if [ -z "$1" ]; then
    echo "Error: Please provide version number as argument"
    echo "Usage: ./build_deploy_local.sh 1.0.0"
    exit 1
fi

# Set version override
export SETUPTOOLS_SCM_PRETEND_VERSION=$1

# Install dependencies and build executables
python -m pip install -e .[dev]

# Build distribution package
python -m pip install --upgrade build twine
python -m build

# Upload to PyPI (will prompt for credentials)
echo "Ready to upload version $1 to PyPI"
read -p "Continue? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    twine upload dist/*
else
    echo "Upload cancelled"
fi
