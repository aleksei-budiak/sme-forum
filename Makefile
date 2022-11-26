.PHONY: target clean all install sync shell build invoke run check lint test cfnlint

#############################################
#											 #
# SAMPLE - Makefile to abstract common tasks #
#											 #
##############################################

PIPENV ?= pipenv

#################
#  Python vars	#
#################

EVENT ?= event_not_defined
FUNCTION ?= function_not_defined

#############
# SAM vars	#
#############

NETWORK = ""

target:
	$(info ${HELP_MESSAGE})
	@exit 0

clean: ##=> Deletes latest build
	$(info [*] Who needs all that anyway? Destroying artifacts....)
	rm -rf ./.aws-sam/
	rm -f ./dependencies/requirements.txt

all: clean build

Pipfile.lock: install

install:
	$(info [*] Installing development packages...)
	@$(PIPENV) install --dev

sync: Pipfile.lock
	$(info [*] Syncing development packages...)
	@$(PIPENV) sync --dev

shell:
	@$(PIPENV) shell

build: ##=> Generates build artifacts for local development/deployment
	@$(MAKE) _install_deps
ifeq ($(DOCKER),1)
	$(info [+] Building all functions available in template.yaml using Docker Lambda -- This may take a while...)
	sam build --use-container
else
	$(info [+] Building all functions available in template.yaml -- This may take a while...)
	sam build
endif

invoke: _check_function_definition _check_event_definition ##=> Run SAM Local function with a given event payload
	@sam local invoke ${FUNCTION} --event ${EVENT}

run: ##=> Run SAM Local API GW and can optionally run new containers connected to a defined network
	$(info [+] Starting Local API Gateway service)
	@test -z ${NETWORK} \
		&& sam local start-api \
		|| sam local start-api --docker-network ${NETWORK}

check: lint test cfnlint openapi-validate

lint:
	$(info [*] Running linters...)
	@$(PIPENV) run python -m pyflakes src

test: export POWERTOOLS_TRACE_DISABLED = true
test:
	@mkdir -p build
	$(info [*] Running tests...)
	@$(PIPENV) run python -m pytest -ra --cov=src --cov-branch --cov-report term-missing \
                                   --html=build/test-results/report.html --self-contained-html \
                                   --junitxml=build/test-results/report.xml \
                                   --cov-report html:build/coverage/html \
                                   --cov-report xml:build/coverage/coverage.xml

cfnlint:
	$(info [*] Running CloudFormation linter...)
	@$(PIPENV) run python -m cfnlint

.PHONY: openapi-validate
openapi-validate: openapi.yaml
	$(info [*] Running OpenAPI validator...)
	@$(PIPENV) run python -m openapi_spec_validator openapi.yaml


#############
#  Helpers  #
#############

_check_function_definition:
	$(info [*] Checking whether function $(FUNCTION) exists...)

# FUNCTION="<name_of_function>" must be passed as ARG for target or else fail
ifndef FUNCTION
	$(error [!] FUNCTION env not defined...FAIL)
endif

_check_event_definition:
	$(info [*] Checking whether event $(EVENT) exists...)

# EVENT="<name_and_path_of_event>" must be passed as ARG for target or else fail
ifndef EVENT
	$(error [!] EVENT env not defined...FAIL)
endif

ifeq ($(wildcard $(EVENT)),)
	$(error [!] '$(EVENT)' file doesn't exist)
endif

_install_deps:
	$(info [+] Installing dependencies...")
	@$(PIPENV) requirements > dependencies/requirements.txt

define HELP_MESSAGE
	Environment variables to be aware of or to hardcode depending on your use case:

	DOCKER
		Default: not_defined
		Info: Environment variable to declare whether Docker should be used to build (great for C-deps)

	FUNCTION
		Default: not_defined
		Info: Environment variable to declare name of the function to invoke

	Common usage:

	...::: Installs development packages required for testing :::...
	$ make install

	...::: Spawn a virtual environment shell :::...
	$ make shell

	...::: Generates build artifacts for local development/deployment :::...
	$ make build

	...::: Generates build artifacts for local development/deployment using a Docker container :::...
	$ make build DOCKER=1

	...::: Run Pytest under tests/ with pipenv :::...
	$ make test

	...::: Cleans up the environment - Deletes locally built artifacts from all functions :::...
	$ make lint

	...::: Running  linters  cfn_lint, pyflakes :::...
	$ make clean

	Advanced usage:

	...::: Run SAM Local API Gateway within a Docker Network :::...
	$ make run NETWORK="sam-network"
endef
