
# Project bootstrap PlayMaker WebApp

Backend side for PlayMaker project.

# Installation

To set up a development environment quickly you need to have following prerequisits:
- Python ^3.8
- poetry in version `1.6.1`
- makefile (NOTE: Windows users have to install it manually via chocolatey. See: https://chocolatey.org/install#individual)
- PostgreSQL (latest) / docker deamon

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

- Migrate old voivodeship field to new one (Voivodeships model)
```bash
python manage.py map_vivos
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

## Standalone scripts:
Scripts from *tools/scripts*. Respectively as .sh (linux) and .bat (windows).
- **initialize_db** - run initial scripts on unmodified database created from dump.


## Additional tools:

- Sentry: Debug tool available at https://playmaker-pro.sentry.io. You can enable sentry by setting `SENTRY_DSN` and `ENABLE_SENTRY` flag in your `.env` file.