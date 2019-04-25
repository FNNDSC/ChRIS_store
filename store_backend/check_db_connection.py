#!/usr/bin/env python

import time
import MySQLdb

db = None
max_tries = 20
while max_tries > 0 and db is None:
    try:
        db = MySQLdb.connect(user="root",
                     passwd="rootp",
                     host="chris_store_dev_db")
    except Exception:
        time.sleep(2)
        max_tries -= 1

if db is None:
    print('Could not connect to database service!')
else:
    print('Database service ready to accept connections!')
