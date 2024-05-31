# Makefile to help automate key steps of the non-NCI process

.PHONY: virtual-environment
virtual-environment:  ## update virtual environment, create a new one if it doesn't already exist
	# Put virtual environments in the project
	poetry config virtualenvs.in-project true
	poetry install --all-extras


data/geog: scripts/download-geog.sh ## Download static geography data
	./scripts/download-geog.sh

.PHONY: clean
clean: ## Remove any previous local runs
	find templates -name "*.d??.nc" -delete
	rm -rf data/runs
	rm -rf data/cmaq
	rm -rf data/mcip

run: ## Run the required steps
	docker run --rm -it -v $(PWD):/opt/project setup_wrf python setup_for_wrf.py -c config.docker.json
	docker run --rm -it -v $(PWD):/opt/project setup_wrf /opt/project/data/runs/aust-test/main.sh
	docker run --rm -it -v $(PWD):/opt/project setup_wrf python setupCMAQinputs.py