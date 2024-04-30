# Makefile to help automate key steps of the non-NCI process

.PHONY: virtual-environment
virtual-environment:  ## update virtual environment, create a new one if it doesn't already exist
	# Put virtual environments in the project
	poetry config virtualenvs.in-project true
	poetry install --all-extras


data/geog: ## Download static geography data
	mkdir -p data/geog
	curl https://www2.mmm.ucar.edu/wrf/src/wps_files/geog_high_res_mandatory.tar.gz -o data/geog/geog_high_res_mandatory.tar.gz
	tar -xvzf data/geog/geog_high_res_mandatory.tar.gz -C data/geog
