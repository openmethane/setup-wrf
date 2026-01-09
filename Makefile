ifneq (, $(shell command -v uv))
	RUN_CMD := uv run
	PYTHON_CMD := uv run python
else
	RUN_CMD :=
	PYTHON_CMD := python
endif

TEST_DIRS := tests/unit

.PHONY: install
install:  ## create virtual env and fetch project dependencies
	uv sync

.PHONY: format
format:  ## format project source files according to ruff config
	uv format

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
	docker run --rm -it -v $(PWD):/opt/project setup_wrf python scripts/setup_for_wrf.py -c config/config.docker.json
	docker run --rm -it -v $(PWD):/opt/project setup_wrf /opt/project/data/runs/aust-test/main.sh

.PHONY: test
test:  ## Run the tests
	$(PYTHON_CMD) -m pytest -r a -v $(TEST_DIRS)

.PHONY: test-regen
test-regen:  ## Regenerate the regression data for tests
	$(PYTHON_CMD) -m pytest -r a -v $(TEST_DIRS) --regen-all

.PHONY: changelog-draft
changelog-draft:  ## compile a draft of the next changelog
	uv run towncrier build --draft

