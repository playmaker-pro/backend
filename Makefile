SHELL = /bin/bash

.PHONY: setup
setup:
	poetry install

.PHONY: test
test:
	poetry run pytest .


.PHONY: export_requirements
export_requirements:
	poetry export -f requirements.txt --output requirements.txt --without-hashes


.PHONY: export_requirements
export_dev_requirements:
	poetry export -f requirements.txt --output requirements.txt --without-hashes


.PHONY: run
run:
	docker compose -f compose/docker-compose-pg-only.yml up -d
