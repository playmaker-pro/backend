
# PlayMaker API

## Installation

To set up a development environment quickly you need to have following prerequisits:
- Python ^3.8
- poetry in version `1.8.2`
- makefile (NOTE: Windows users have to install it manually via chocolatey. See: https://chocolatey.org/install#individual)
- PostgreSQL (16)
- Redis (6)
- MongoDB (6)
- Docker & Docker-compose (to run PostgreSQL, Redis and MongoDB in containers)

## Bootstrap project:

1. `make setup python_path={python interpreter system path}` - to initialize poetry and create an virtual environment
2. `make start-db` - to start postgresql docker container
3. Copy EXAMPLE.env content to .env file and fill it with your data.

for other commands see `Makefile`

**_NOTE:_**

    If you want to use local postgres database instead of docker container, you have to change credentials in .env file.


## Extra scripts:

- Fill DB with voivodeships.
```bash
python manage.py add_voivodeships
```

- Migrate the cities_light app
```bash
python manage.py migrate cities_light
```

- To update the cities data, run the following command provided by django-cities-light
```bash
python manage.py cities_light
```

- To generate short names for clubs and teams
```bash
python manage.py create_short_name_for_club_and_team
```

- To generate language translation, you have to compile .po files:
```bash
python manage.py compilemessages
```

- To populate address details for all clubs
```bash
python manage.py populate_club_address_details
```

## Docker
To run the application in docker container, run:
```bash
docker compose up --build
```

To execute commands inside the container, run:
```bash
docker compose exec playmaker YOUR_COMMAND
```

To import database dump, run:
```bash
docker cp dump.sql playmaker-postgres:/dump.sql
docker exec -i playmaker-postgres psql -U DB_USER -d DB_NAME -f /dump.sql
```

## Celery

To use Celery for background task processing, you have two options:

1. Run the Django development server with Celery integrated:
```bash
python manage.py runserver --celery
```

2. Run Celery in a separate terminal:
```bash
python manage.py celery
```

## Additional tools:

- Sentry: Debug tool available at https://playmaker-pro.sentry.io. You can enable sentry by setting `SENTRY_DSN` and `ENABLE_SENTRY` flag in your `.env` file.