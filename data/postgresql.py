import psycopg2
import json
import datetime

now = datetime.datetime.now().strftime('%d/%m %H:%M')

with open("config.json", "r", encoding="utf-8") as f:
    cfg = json.load(f)

try:
    connection = psycopg2.connect(
        host=cfg['PostgreSQL']['host'],
        user=cfg['PostgreSQL']['user'],
        password=cfg['PostgreSQL']['password'],
        database=cfg['PostgreSQL']['database']
    )

    print(f'[POSTGRESQL] [INFO] [{now}] CONNECT SUCCESSFULLY')
    cursor = connection.cursor()
    connection.autocommit = True
except psycopg2.Error as e:
    print(f'[POSTGRESQL] [ERROR] [{now}] CONNECT FAILED AS ERROR: {e}')
