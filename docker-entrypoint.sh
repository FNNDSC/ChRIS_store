#!/bin/bash

# Set the permission on the mounted volume container
# chmod 777 /usr/users

# Start ChRIS store server
python check_db_connection.py -u root -p rootp --host chris_store_dev_db --max-attempts 30
python manage.py migrate
#python manage.py runserver 0.0.0.0:8010
#python manage.py collectstatic
python manage.py runmodwsgi --host 0.0.0.0 --port 8010 --server-name localhost --reload-on-changes
#python manage.py runmodwsgi --host 0.0.0.0 --port 8010 --processes 8 --server-name localhost --reload-on-changes

exec "$@"
