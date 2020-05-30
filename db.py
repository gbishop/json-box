"""
db wrapper for json-box
"""
import sqlite3
import os

testing = False

if os.getcwd().startswith("/var/www"):
    DBNAME = "/var/local/json-box/box.db"
else:
    DBNAME = "box.db"

DBFLAGS = sqlite3.PARSE_COLNAMES | sqlite3.PARSE_DECLTYPES


def dict_factory(cursor, row):
    """Return a dict for each row"""
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


# a decorator to manage db access
def with_db(func):
    """Add an extra argument with a database connection"""

    def func_wrapper(*args, **kwargs):
        db = sqlite3.connect(DBNAME, detect_types=DBFLAGS)
        db.row_factory = dict_factory
        result = func(*args, **dict(kwargs, db=db))
        db.commit()
        db.close()
        return result

    return func_wrapper


def insert(db, table, insertVerb="insert", **fields):
    """Insert an record into a table"""
    sql = "%s into %s (%s) values (%s)" % (
        insertVerb,
        table,
        ", ".join(fields.keys()),
        ", ".join(["?"] * len(fields)),
    )
    return db.execute(sql, tuple(fields.values()))


@with_db
def createTables(db):
    # marked points
    db.execute(
        """create table if not exists drops
        (id integer primary key,
         time timestamp,
         json text,
         deleted integer -- 1 if deleted
        )"""
    )


createTables()
