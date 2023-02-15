""" database access
docs:
* http://initd.org/psycopg/docs/
* http://initd.org/psycopg/docs/pool.html
* http://initd.org/psycopg/docs/extras.html#dictionary-like-cursor
"""

from contextlib import contextmanager
import logging
import os

import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import DictCursor

pool = None

def setup():
    global pool
    DATABASE_URL = os.environ['DATABASE_URL']
    pool = ThreadedConnectionPool(1, 100, dsn=DATABASE_URL, sslmode='require')


@contextmanager
def get_db_connection():
    try:
        connection = pool.getconn()
        yield connection
    finally:
        pool.putconn(connection)


@contextmanager
def get_db_cursor(commit=False):
    with get_db_connection() as connection:
      cursor = connection.cursor(cursor_factory=DictCursor)
      try:
          yield cursor
          if commit:
              connection.commit()
      finally:
          cursor.close()

def add_survey_response_no_suggestion(user_name, topping, chain):
    with get_db_cursor(True) as cur:
        cur.execute(
            "INSERT INTO survey_responses (user_name, topping, chain) values (%s, %s, %s)",
            (user_name, topping, chain)
            )
        
def add_survey_response_with_suggestion(user_name, topping, chain, suggestion):
    with get_db_cursor(True) as cur:
        cur.execute(
            """INSERT INTO survey_responses (user_name, topping, chain, suggestion)
            values (%s, %s, %s, %s)""",
            (user_name, topping, chain, suggestion)
            )

def get_all_survey_responses():
    with get_db_cursor(False) as cur:
        cur.execute(
            "SELECT * FROM survey_responses ORDER BY id ASC"
        )
        return cur.fetchall()

def get_all_survey_responses_reverse():
    with get_db_cursor(False) as cur:
        cur.execute(
            "SELECT * FROM survey_responses ORDER BY id DESC"
        )
        return cur.fetchall()

def remove_all_responses():
    with get_db_cursor(True) as cur:
        cur.execute(
            "DELETE FROM survey_responses"
        )

if __name__ == "__main__":
    setup()
    remove_all_responses()
    add_survey_response_no_suggestion('kafka050', 'mushrooms', 'punch')
    add_survey_response_with_suggestion('bob bobberson', 'pepperoni', 'pizza hut', 'suggestion')

    print(get_all_survey_responses())
    print(get_all_survey_responses_reverse())
