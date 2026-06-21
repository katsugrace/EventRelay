#!/bin/bash

set -e

mkdir -p assets

if command -v flake8 >/dev/null 2>&1; then
	flake8 src tests
else
	if python3 -m flake8 --version >/dev/null 2>&1; then
		python3 -m flake8 src tests
	fi
fi

python3 -m pytest --cov=src --cov-report=xml

genbadge coverage -i coverage.xml -o assets/coverage-badge.svg
