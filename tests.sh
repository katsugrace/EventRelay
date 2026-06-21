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

if command -v coverage-badge >/dev/null 2>&1; then
	coverage-badge -f -o assets/coverage-badge.svg
else
	if python3 -m coverage_badge -h >/dev/null 2>&1; then
		python3 -m coverage_badge -f -o assets/coverage-badge.svg
	else
		exit 0
	fi
fi
