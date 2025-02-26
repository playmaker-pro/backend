SHELL = /bin/bash


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


.PHONY: restart
restart:
	touch tmp/restart.txt


.PHONY: migrate
migrate:
	poetry run python manage.py migrate

