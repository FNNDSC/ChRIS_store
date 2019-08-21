#!/bin/bash

# Start ChRIS store server
python check_db_connection.py -u root -p rootp --host chris_store_dev_db --max-attempts 30
python manage.py migrate
#python manage.py collectstatic
mod_wsgi-express start-server config/wsgi.py --host 0.0.0.0 --port 8010 --processes 8 --server-root ~/mod_wsgi-0.0.0.0:8010
#mod_wsgi-express setup-server config/wsgi.py --host 0.0.0.0 --port 8010 --processes 8 --server-name localhost --server-root ~/mod_wsgi-0.0.0.0:8010
#to start daemon:
#~/mod_wsgi-0.0.0.0:8010/apachectl start
#to stop deamon
#~/mod_wsgi-0.0.0.0:8010/apachectl stop

exec "$@"
