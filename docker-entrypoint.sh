#!/bin/bash

# Set the permission on the mounted volume container
# chmod 777 /usr/users

# Start ChRIS store server
python check_db_connection.py
python manage.py migrate
python manage.py runserver 0.0.0.0:8010

exec "$@"
