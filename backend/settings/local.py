DATABASES = {
    # 'default': {
    #     'ENGINE': 'django.db.backends.sqlite3',
    #     'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    # },
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'local_pm',
        'USER': 'arsen',
        'PASSWORD': 'postgres',
        'HOST': 'localhost',
        'PORT': '5432',
    },
    'datadb': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'local_data',
        'USER': 'arsen',
        'PASSWORD': 'postgres',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
DATABASES['datadb'] = {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'p1390_pm1',
        'USER': 'p1390_pm1',
        'PASSWORD': 'H6ZBRHlEKe5ILtvCalaa',
        'HOST': 'localhost',
        'PORT': '8543 '  # '9543',  # ssh -f jacekplaymaker@s38.mydevil.net -L 8543:pgsql38.mydevil.net:5432 -N
}
