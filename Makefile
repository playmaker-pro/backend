SHELL := /bin/bash
LOG_DIR=.logs
CELERY_LOG=$(LOG_DIR)/celery_worker.log
BEAT_LOG=$(LOG_DIR)/celery_beat.log
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
restart: stop start

.PHONY: stop
stop: stop-celery

.PHONY: start
start: start-celery

restart-touch: tmp/restart.txt
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
	@echo "Starting Celery worker with watchdog in screen session celery-worker..."
	screen -dmS celery-worker bash bin/celery_worker_watchdog.sh "$(CELERY_LOG)"
	@echo "Celery worker started. Attach with: screen -r celery-worker"

.PHONY: stop-celery-worker
stop-celery-worker:
	@echo "Stopping Celery worker..."
	@screen -X -S celery-worker quit 2>/dev/null || true
	@pkill -f 'celery -A backend worker' 2>/dev/null || true
	@sleep 1
	@echo "Celery worker stopped."

.PHONY: start-celery-beat
start-celery-beat: ensure-logs
	@echo "Starting Celery Beat with watchdog in screen session celery-beat..."
	screen -dmS celery-beat bash bin/celery_beat_watchdog.sh "$(BEAT_LOG)" "$(BEAT_PID_FILE)"
	@echo "Celery beat started. Attach with: screen -r celery-beat"

.PHONY: stop-celery-beat
stop-celery-beat:
	@echo "Stopping Celery Beat..."
	@screen -X -S celery-beat quit 2>/dev/null || true
	@if [ -f $(BEAT_PID_FILE) ]; then kill $$(cat $(BEAT_PID_FILE)) 2>/dev/null || true; fi
	@pkill -f 'celery -A backend beat' 2>/dev/null || true
	@rm -f $(BEAT_PID_FILE) 2>/dev/null || true
	@sleep 1
	@echo "Celery beat stopped."

.PHONY: status-celery
status-celery:
	@echo "=== Celery Status ==="
	@echo ""
	@echo "Screen sessions:"
	@screen -ls | grep -E "celery-(worker|beat)" || echo "  No screen sessions found"
	@echo ""
	@echo "Celery processes:"
	@ps aux | grep -E "celery -A backend" | grep -v grep || echo "  No celery processes found"
	@echo ""
	@echo "PID files:"
	@ls -la $(BEAT_PID_FILE) 2>/dev/null || echo "  No beat PID file found"

.PHONY: logs-celery-worker
logs-celery-worker:
	@tail -f $(CELERY_LOG)

.PHONY: logs-celery-beat
logs-celery-beat:
	@tail -f $(BEAT_LOG)

.PHONY: attach-celery-worker
attach-celery-worker:
	@screen -r celery-worker

.PHONY: attach-celery-beat
attach-celery-beat:
	@screen -r celery-beat


.PHONY: shell
shell:
	poetry run python manage.py shell


.PHONY: server
server:
	poetry run python manage.py runserver --celery


.PHONY: postman
postman:
	poetry run python manage.py postman