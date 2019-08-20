#!/bin/bash

# Start ChRIS store development server
python check_db_connection.py -u root -p rootp --host chris_store_dev_db --max-attempts 30
python manage.py migrate
python manage.py runserver 0.0.0.0:8010
#python manage.py collectstatic
#python manage.py runmodwsgi --working-directory $(pwd) --host 0.0.0.0 --port 8010 --server-name localhost --server-root ~/mod_wsgi-0.0.0.0:8010 --reload-on-changes

exec "$@"
