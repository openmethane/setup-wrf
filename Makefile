# Makefile to help automate key steps of the non-NCI process

.PHONY: virtual-environment
virtual-environment:  ## update virtual environment, create a new one if it doesn't already exist
	poetry lock --no-update
	# Exclude the virtual environment from the project
	poetry config virtualenvs.in-project false
	poetry install --all-extras
	# TODO: Add last line back in when pre-commit is set up
	# poetry run pre-commit install


data/geog: scripts/download-geog.sh ## Download static geography data
	./scripts/download-geog.sh

.PHONY: clean
clean: ## Remove any previous local runs
	find templates -name "*.d??.nc" -delete
	rm -rf data/runs
	rm -rf data/cmaq
	rm -rf data/mcip

run: ## Run the required steps
	docker run --rm -it -v $(PWD):/opt/project setup_wrf python scripts/setup_for_wrf.py -c config.docker.json
	docker run --rm -it -v $(PWD):/opt/project setup_wrf /opt/project/data/runs/aust-test/main.sh
	docker run --rm -it -v $(PWD):/opt/project setup_wrf python scripts/setup_for_CMAQ.py