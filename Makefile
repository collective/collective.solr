# keep in sync with: https://github.com/kitconcept/buildout/edit/master/Makefile
# update by running 'make update'
SHELL := /bin/bash
CURRENT_DIR:=$(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))

version = 3

# We like colors
# From: https://coderwall.com/p/izxssa/colored-makefile-for-golang-projects
RED=`tput setaf 1`
GREEN=`tput setaf 2`
RESET=`tput sgr0`
YELLOW=`tput setaf 3`

all: .installed.cfg

# Add the following 'help' target to your Makefile
# And add help text after each target name starting with '\#\#'
.PHONY: help
help: ## This help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'


.installed.cfg: .venv/bin/buildout *.cfg
	.venv/bin/buildout

.venv/bin/buildout: .venv/bin/pip3
	.venv/bin/pip install -r requirements-6.1.x.txt
	.venv/bin/pip install click==8.0.4 black==21.10b0 || true
	.venv/bin/pip install tomli==2.3.0 || true
	@touch -c $@

.venv/bin/pip3:
	python$(version) -m venv .venv

.PHONY: Build Plone 6.0
build-plone-6.0: .installed.cfg  ## Build Plone 6.0
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements-6.0.txt
	.venv/bin/buildout -c plone-6.0.x.cfg

.PHONY: Build Plone 6.1
build-plone-6.1: .installed.cfg  ## Build Plone 6.1
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements-6.1.x.txt
	.venv/bin/buildout -c plone-6.1.x.cfg

.PHONY: Test
test:  ## Test
	.venv/bin/pip install zest.pocompile
	.venv/bin/pocompile src
	./bin/test

.PHONY: Test Performance
test-performance:
	jmeter -n -t performance.jmx -l jmeter.jtl

.PHONY: Code Analysis
code-analysis:  ## Code Analysis
	if [ -f "bin/black" ]; then bin/black src/ --check ; fi

.PHONY: Black
black:  ## Black
	if [ -f "bin/black" ]; then bin/black src/ ; fi

.PHONY: Build Docs
docs:  ## Build Docs
	bin/sphinxbuilder

.PHONY: Test Release
test-release:  ## Run Pyroma and Check Manifest
	bin/pyroma -n 10 -d .

.PHONY: Start Backend
start-backend:  ## Start Plone Backend
	bin/instance fg

.PHONY: Start Solr
start-solr:  ## Start Solr
	bin/solr-foreground

.PHONY: Release
release:  ## Release
	bin/fullrelease

.PHONY: Clean
clean:  ## Clean
	git clean -Xdf

.PHONY: all clean
