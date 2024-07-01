# Makefile to help automate key steps of the non-NCI process

# Check if we are running in the docker container or not
ifneq (, $(shell which poetry))
	PYTHON_CMD := poetry run python
else
	PYTHON_CMD := python
endif

TEST_DIRS := tests/unit

.PHONY: virtual-environment
virtual-environment:  ## update virtual environment, create a new one if it doesn't already exist
	poetry lock --no-update
	# Exclude the virtual environment from the project
	poetry config virtualenvs.in-project false
	poetry install --all-extras
	# TODO: Add last line back in when pre-commit is set up
	# poetry run pre-commit install

.PHONY: ruff-fixes
ruff-fixes:  # Run ruff on the project
 	# Run the formatting first to ensure that is applied even if the checks fail
	poetry run ruff format .
	poetry run ruff check --fix .
	poetry run ruff format .

data/geog: scripts/download-geog.sh ## Download static geography data
	./scripts/download-geog.sh

.PHONY: clean
clean: ## Remove any previous local runs
	find data/runs ! -path '*/metem/*' -delete  # exclude the pre downloaded met data

.PHONY: build
build:  ## Build the docker container locally
	docker build --platform=linux/amd64 -t setup_wrf .

.PHONY: run
run: build  ## Run the required steps for the test domain
	docker run --rm -it -v $(PWD):/opt/project setup_wrf python scripts/setup_for_wrf.py -c config/wrf/config.docker.json
	docker run --rm -it -v $(PWD):/opt/project setup_wrf /opt/project/data/runs/aust-test/main.sh

.PHONY: test
test:  ## Run the tests
	$(PYTHON_CMD) -m pytest -r a -v $(TEST_DIRS)

.PHONY: test-regen
test-regen:  ## Regenerate the regression data for tests
	$(PYTHON_CMD) -m pytest -r a -v $(TEST_DIRS) --regen-all
