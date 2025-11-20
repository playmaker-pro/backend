SHELL := /bin/bash
LOG_DIR=.logs
CELERY_LOG=$(LOG_DIR)/celery_worker.log
BEAT_LOG=$(LOG_DIR)/celery_beat.log
WORKER_PID_FILE := .celery-worker.pid
BEAT_PID_FILE := .celerybeat.pid

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
restart: stop start tmp/restart.txt
stop: stop-celery stop-celery-beat
start: start-celery start-celery-beat
tmp/restart.txt:
	@mkdir -p tmp
	@touch tmp/restart.txt


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
	nohup poetry run celery -A backend worker --pidfile $(WORKER_PID_FILE) \
	--autoscale=1,6 --without-mingle --without-gossip --loglevel=DEBUG \
	--max-tasks-per-child=1000 --task-events --pool=prefork > $(CELERY_LOG) 2>&1 &

.PHONY: stop-celery-worker
stop-celery-worker:
	@echo "Stopping Celery worker..."
	@if [ -f $(WORKER_PID_FILE) ]; then \
		kill -TERM $$(cat $(WORKER_PID_FILE)) || true; \
		sleep 2; \
		if kill -0 $$(cat $(WORKER_PID_FILE)) 2>/dev/null; then kill -KILL $$(cat $(WORKER_PID_FILE)) || true; fi; \
		rm -f $(WORKER_PID_FILE); \
		echo "Celery worker stopped."; \
	else \
		echo "No worker PID file found. Attempting remote shutdown if any worker responds..."; \
		poetry run celery -A backend inspect ping >/dev/null 2>&1 && poetry run celery -A backend control shutdown || echo "No active worker responded; skip."; \
	fi

.PHONY: start-celery-beat
start-celery-beat: ensure-logs
	@echo "Starting Celery Beat in background session..."
	nohup poetry run celery -A backend beat -l info --scheduler django --pidfile $(BEAT_PID_FILE) > $(BEAT_LOG) 2>&1 &

.PHONY: stop-celery-beat
stop-celery-beat:
	@echo "Stopping Celery Beat..."
	@if [ -f $(BEAT_PID_FILE) ]; then kill -TERM $$(cat $(BEAT_PID_FILE)) || true; rm -f $(BEAT_PID_FILE); echo "Celery beat stopped."; else echo "No beat PID file found (already stopped)."; fi


.PHONY: shell
shell:
	poetry run python manage.py shell


.PHONY: server
server:
	poetry run python manage.py runserver --celery


.PHONY: postman
postman:
	poetry run python manage.py postman