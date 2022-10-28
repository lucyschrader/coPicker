import sqlite3
from sqlite3 import Error
import click
from flask import current_app, g

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)

def init_db():
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

@click.command('init-db')
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db

def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def write_new(statement, value, message):
    db = get_db()
    cursor = db.cursor()
    error = None

    try:
        cursor.execute(statement, value)
        db.commit()

        return message
    
    except Error as e:
        print(e)
        print(statement, value)

def query_db(statement, args=(), one=False):
    db = get_db()
    cur = db.execute(statement, args)
    data = cur.fetchall()
    return (data[0] if data else None) if one else data

def update_item(statement, args=(), message=None):
    db = get_db()

    try:
        db.execute(statement, args)
        db.commit()

        return message

    except db.IntegrityError:
        return None

def delete_item(statement, value, message):
    db = get_db()
    db.execute(statement, (value,))
    db.commit()

    return message