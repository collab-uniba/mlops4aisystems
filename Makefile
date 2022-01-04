NAME := actions4DS
INSTALL_STAMP := .install.stamp
PRODUCTION_STAMP := .production.stamp
EXPORT_STAMP := .export.stamp
PRECOMMIT_CONF := .pre-commit-config.yaml
SRC := $(NAME)
POETRY := $(shell command -v poetry 2> /dev/null)

.DEFAULT_GOAL := help

.PHONY: help
help:
	@echo "Please use 'make <target>' where <target> is one of"
	@echo ""
	@echo "  install     		install packages and prepare the development environment"
	@echo "  update      		force-udpate packages and prepare the development environment"
	@echo "  production  		install packages and prepare the production environment"
	@echo "  export      		export all requirements to requirements.txt"
	@echo "  clean       		remove all temporary files"
	@echo "  format      		reformat code"
	@echo "  lint|precommit   	run the pre-commit checks on all files"
	@echo ""

install: $(INSTALL_STAMP)
$(INSTALL_STAMP): pyproject.toml
	@if [ -z $(POETRY) ]; then echo "Poetry could not be found. See https://python-poetry.org/docs/"; exit 2; fi
	$(POETRY) install --no-root
	$(POETRY) lock --no-update
	$(POETRY) run pre-commit install
	touch $(INSTALL_STAMP)

update: pyproject.toml
	@if [ -z $(POETRY) ]; then echo "Poetry could not be found. See https://python-poetry.org/docs/"; exit 2; fi
	$(POETRY) update
	$(POETRY) lock --no-update
	$(POETRY) run pre-commit install
	$(POETRY) run pre-commit autoupdate
	touch $(INSTALL_STAMP)

production: $(PRODUCTION_STAMP)
$(PRODUCTION_STAMP): pyproject.toml poetry.lock
	@if [ -z $(POETRY) ]; then echo "Poetry could not be found. See https://python-poetry.org/docs/"; exit 2; fi
	$(POETRY) install --no-root --without dev --no-interaction
	touch $(PRODUCTION_STAMP)

export: $(EXPORT_STAMP)
$(EXPORT_STAMP): pyproject.toml poetry.lock
	@if [ -z $(POETRY) ]; then echo "Poetry could not be found. See https://python-poetry.org/docs/"; exit 2; fi
	$(POETRY) export -f requirements.txt --output requirements-dev.txt --dev --without-hashes
	$(POETRY) export -f requirements.txt --output requirements.txt --without-hashes
	touch $(EXPORT_STAMP)

.PHONY: clean
clean:
	find . -type d -name "__pycache__" | xargs rm -rf {};
	rm -rf $(INSTALL_STAMP) $(PRODUCTION_STAMP) $(EXPORT_STAMP) .mypy_cache

.PHONY: format
format: $(INSTALL_STAMP)
	$(POETRY) run isort $(SRC)
	$(POETRY) run black $(SRC)

.PHONY: lint
lint: precommit

.PHONY: precommit
precommit: $(INSTALL_STAMP) $(PRECOMMIT_CONF)
	$(POETRY) run pre-commit run --all-files
