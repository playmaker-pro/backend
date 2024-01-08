
# Project bootstrap PlayMaker WebApp

Backend side for PlayMaker project.

# Installation

To set up a development environment quickly you need to have following prerequisits:
> Python 3.8.2
> poetry in version `1.6.1`
> makefile
> PostgreSQL (latest)

## Bootstrap project:


`make setup`
`make run`

for other commands see `Makefile`



Create local env file
    If you use defauly postgres settings, ofc you need to create database (for example: local_pm)  and allow user to use it.

    `backend/settings/local.py`
    ```
    CONFIGURATION = 'dev'
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'local_pm',
            'USER': 'jacek',
            'PASSWORD': 'postgres',
            'HOST': 'localhost',
            'PORT': '5432',
        },
   }
   SYSTEM_USER_EMAIL = "your_admin_email"
    ```

11. To have database synced with production or staging, you have to fill DB with voivodeships.
    ```
    python manage.py add_voivodeships
    ```


## Extra scripts:

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

## Standalone scripts:
Scripts from *tools/scripts*. Respectively as .sh (linux) and .bat (windows).
- **create_dotenv_template** - create empty .env template file inside project root directory.
- **initialize_db** - run initial scripts on unmodified database created from dump.
