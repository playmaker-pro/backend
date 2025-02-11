SHELL = /bin/bash

.PHONY: setup
setup:
ifeq ($(OS),Windows_NT)
	@if not exist "_logs" mkdir "_logs"
	poetry env use $(python_path)
	poetry install
else
	[ -d "_logs" ] || mkdir -p _logs
	poetry env use $(python_path)
	poetry install
endif


.PHONY: test
test:
	poetry run pytest .


.PHONY: export_requirements
export_requirements:
	make export_base_requirements
	make export_dev_requirements


.PHONY: export_base_requirements
export_base_requirements:
	poetry export -f requirements.txt --output requirements.txt --without-hashes


.PHONY: export_requirements
export_dev_requirements:
	poetry export --without-hashes -f requirements.txt --only=dev --output requirements.dev.txt


.PHONY: start-db
start-db:
	docker compose -f docker-compose.yml up -d


.PHONY: startapp
startapp:
	python manage.py runserver