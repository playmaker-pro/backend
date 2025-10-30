SHELL = /bin/bash
LOG_DIR=_logs
CELERY_LOG=$(LOG_DIR)/celery_worker.log
BEAT_LOG=$(LOG_DIR)/celery_beat.log

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


.PHONY: restart stop start start-celery stop-celery start-celery-beat stop-celery-beat
restart: tmp/restart.txt stop start
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
start-celery: ensure-logs
	@nohup bash -c '\
	while true; do \
		echo "Starting Celery worker..."; \
		poetry run celery -A backend worker --autoscale=0,6 --without-mingle --without-gossip --loglevel=INFO >> $(CELERY_LOG) 2>&1; \
		echo "Celery worker crashed. Restarting in 5s..." >> $(CELERY_LOG); \
		sleep 5; \
	done' > /dev/null 2>&1 &

.PHONY: stop-celery
stop-celery:
	@echo "Stopping Celery worker..."
	@pkill -f 'celery -A backend worker' || true

.PHONY: start-celery-beat
start-celery-beat: ensure-logs
	@nohup bash -c '\
	while true; do \
		echo "Starting Celery beat..."; \
		poetry run celery -A backend beat -l info --scheduler django --pidfile .celerybeat.pid >> $(BEAT_LOG) 2>&1; \
		echo "Celery beat crashed. Restarting in 5s..." >> $(BEAT_LOG); \
		sleep 5; \
	done' > /dev/null 2>&1 &

.PHONY: stop-celery-beat
stop-celery-beat:
	@echo "Stopping Celery Beat..."
	@pkill -f 'celery -A backend beat' || true


.PHONY: shell
shell:
	poetry run python manage.py shell


.PHONY: server
server:
	poetry run python manage.py runserver --celery


.PHONY: postman
postman:
	poetry run python manage.py postman