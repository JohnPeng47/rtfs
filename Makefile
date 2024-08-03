# Makefile for building and uploading Python package
PYTHON = python
PACKAGE_NAME = rtfs
TWINE = twine

# Clean up build artifacts
clean:
	rm -rf build dist *.egg-info

# Build the package
build: clean
	$(PYTHON) -m build

# Upload to PyPI using twine
upload: build
	$(TWINE) upload dist/*

# Install locally for testing
install: build
	pip install dist/$(PACKAGE_NAME)-*.whl

# Default target
all: build

.PHONY: clean build upload install all