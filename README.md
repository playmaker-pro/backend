
# Project bootstrap PlayMaker WebApp

Backend side for PlayMaker project.

#### Applications and their roles
1. Features
    * Application for managing user features permissions. Core job is to provide a way to manage user permissions for features.
    * Basically application says, what role can access what feature. For example, we can define there limitations for viewing specific views

# Installation

To set up a development environment quickly you need to have following prerequisits:
> Python 3.8

> PostgreSQL (latest)

## Steps:


1. Create and activate virtualenv for `python 3.8.x` ([see more](https://docs.python.org/3.8/library/venv.html))

2. Create workspace directories
    ```
    mkdir /pm
    cd pm
    mkdir packages/
    ```
3. Clone repository and initialize submodules
    ```
    git clone https://gitlab.com/playmaker1/webapp --recurse-submodules
    ```

4. Clone additional packages and install as a in-develop packages
    ````
    git clone https://gitlab.com/playmaker1/packages/pm-stream-framework
    git clone https://gitlab.com/playmaker1/packages/pm-core
    ````

5. Install all dependencies:
    **Please follow order of installation!**
    > Note that use_2to3 not working with newest setuptools, so before installing dependencies, you have to install lower version
    ```
    cd webapp
    (vn) pip install "setuptools<58.0"
    (vn) pip install -r requirements.txt
    (vn) pip install celery==3.1.26.post2
    (vn) pip install -r requirement_dev.txt
    ```

    Then we need to add custom version of a streamer library. (please note that this is a directory to which we cloned repository from 4.)
    ```
    cd ..
    cd package/pm-stream-framework
    (vn) pip install -e .
    cd ../pm-core
    (vn) pip install -e .
    ```
    > **pm-core package installation in this case is a temporary solution until proper pypi server will be setup<br><br>**
    Note: ignore error about django-celery incompatibility. <br>
    Note: If you are Windows user, you have to install additional library: (vn)  pip install windows-curses

    Now you can verify if everything is fine you should see:
    ```
    python manage.py check

    :: loading dev configuration
    SEO data loaded from seo.yaml
    No local settings. No module named 'backend.settings.local'
    >> Loading app settings: data.app_settings app settings laoded
    ...

    ```
6. Create local env file
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
7. Run migrations:
    ```
    python manage.py migrate
    ```
8. Create super-user (and follow pop-ups)
    ```
    python manage.py createsuperuser
    ```

9. Run development server
    ```
    python manage.py runserver
    ```
10. Go to http://localhost:8000/admin/  (wagtail admin)
    Login into a Admin user (see step no 8)
    Create new page as Main PlaymakerPage
    Create servce with port :8000 and attach main page to that service.

11. To have database synced with production or staging, you have to fill DB with voivodeships.
    ```
    python manage.py add_voivodeships
    ```

# Development

Install dev requirements:
```bash
pip install requirements_dev.txt
```

Working with black formating:

```bash
invoke black
```

Invoke tests:

```bash
pytest .
```
or
```bash
invoke tests
```

#### Extra scripts:

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

#### Run docker

docker compose -f compose/docker-compose-pg-only.yml up -d
