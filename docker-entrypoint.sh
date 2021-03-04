#!/bin/bash

if [[ "$DJANGO_DB_MIGRATE" == 'on' ]]; then
  if [[ "$DJANGO_SETTINGS_MODULE" == 'config.settings.local' ]]; then
    python migratedb.py -u root -p rootp --host chris_store_dev_db --noinput
  elif [[ "$DJANGO_SETTINGS_MODULE" == 'config.settings.production' ]]; then
    python migratedb.py -u root -p $MYSQL_ROOT_PASSWORD --host $DATABASE_HOST --noinput
  fi
fi

exec "$@"
