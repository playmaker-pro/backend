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
	make stop-celery
	make stop-celery-beat
	make start-celery
	make start-celery-beat


.PHONY: migrate
migrate:
	poetry run python manage.py migrate


.PHONY: start-celery
start-celery:
	nohup poetry run celery -A backend worker --autoscale=0,4 --without-mingle --without-gossip > /dev/null 2>&1 &


.PHONY: stop-celery
stop-celery:
	nohup poetry run celery -A backend control shutdown > /dev/null 2>&1 &


.PHONY: start-celery-beat
start-celery-beat:
	nohup poetry run celery -A backend beat -l info --scheduler django --pidfile .celerybeat.pid > /dev/null 2>&1 &


.PHONY: stop-celery-beat
stop-celery-beat:
	kill -9 `cat .celerybeat.pid`


.PHONY: shell
shell:
	poetry run python manage.py shell
