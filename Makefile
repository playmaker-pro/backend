SHELL := /bin/bash
LOG_DIR=.logs
CELERY_LOG=$(LOG_DIR)/celery_worker.log
BEAT_LOG=$(LOG_DIR)/celery_beat.log
BEAT_PID_FILE := .celerybeat-$(PROJECT_NAME).pid

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
	poetry run python manage.py runserver


.PHONY: restart 
restart: tmp/restart.txt stop start
stop: stop-celery stop-celery-beat
start: start-celery start-celery-beat
restart:
	@mkdir -p tmp
	touch tmp/restart.txt


.PHONY: migrate
migrate:
	poetry run python manage.py migrate


.PHONY: ensure-logs
ensure-logs:
	@mkdir -p $(LOG_DIR)

.PHONY: start-celery
start-celery: 
	make start-celery-worker 
	make start-celery-beat

.PHONY: stop-celery
stop-celery: 
	make stop-celery-worker
	make stop-celery-beat

.PHONY: start-celery-worker
start-celery-worker: ensure-logs
	@echo "Starting Celery worker in background session..."
	nohup poetry run celery -A backend \
	worker --autoscale=0,6 --without-mingle --without-gossip --loglevel=DEBUG \
	--max-tasks-per-child=1000 --task-events --pool=prefork > $(CELERY_LOG) 2>&1 &

.PHONY: stop-celery-worker
stop-celery-worker:
	@echo "Stopping Celery worker..."
	celery -A backend control shutdown

.PHONY: start-celery-beat
start-celery-beat: ensure-logs
	@echo "Starting Celery Beat in background session..."
	nohup poetry run celery -A backend beat -l info --scheduler django --pidfile .celerybeat.pid > $(BEAT_LOG) 2>&1 &

.PHONY: stop-celery-beat
stop-celery-beat:
	@echo "Stopping Celery Beat..."
	kill $$(cat .celerybeat.pid)


.PHONY: shell
shell:
	poetry run python manage.py shell


.PHONY: server
server:
	poetry run python manage.py runserver --celery


.PHONY: postman
postman:
	poetry run python manage.py postman