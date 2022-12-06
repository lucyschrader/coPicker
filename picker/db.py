import sqlite3
from sqlite3 import Error
import click
from flask import current_app, g

from werkzeug.security import check_password_hash, generate_password_hash

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(create_user)
    app.cli.add_command(create_project)

def init_db():
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

@click.command('init-db')
def init_db_command(test):
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')


@click.command('create-user')
@click.argument('username')
@click.argument('password')
@click.option('--role', required=True, type=str, default='user', help='set to either user or admin')
def create_user(username, password, role):
    if query_db(statement="SELECT * FROM users WHERE username = ?", args=[username], one=True) == None:
        if role == 'user' or 'admin':
            write_new(statement="INSERT INTO users (username, password, role) VALUES (?, ?, ?)", args=(username, generate_password_hash(password), role))
            click.echo("{} is in the db!".format(username))
        else:
            click.echo("Role needs to be user or admin")
    else:
        click.echo("Username already taken.")

@click.command('create-project')
@click.argument('title')
@click.argument('faceted_title')
def create_project(title, faceted_title):
    if query_db(statement="SELECT * FROM projects WHERE facetedTitle = ?", args=[faceted_title], one=True) == None:
        write_new(statement="INSERT INTO projects (title, facetedTitle) VALUES (?, ?)", args=(title, faceted_title))
        click.echo("{} is in the db!".format(title))
    else:
        click.echo("Project already in db")

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

def write_new(statement, args):
    db = get_db()
    cursor = db.cursor()
    error = None

    try:
        cursor.execute(statement, args)
        db.commit()

        print("DB operation: ", statement, args, " written to db")
        return True
    
    except Error as e:
        print(e)
        print(statement, args)
        return False

def query_db(statement, args=(), one=False):
    db = get_db()
    cur = db.execute(statement, args)
    data = cur.fetchall()
#    print("DB operation: ", statement, args, " query sent to db")
#    print((data[0] if data else None) if one else data)
    return (data[0] if data else None) if one else data

def update_item(statement, args=()):
    db = get_db()

    try:
        db.execute(statement, args)
        db.commit()

        print("DB operation: ", statement, args, " updated in db")

    except db.IntegrityError:
        return None

def delete_item(statement, args):
    db = get_db()
    db.execute(statement, (args,))
    db.commit()

    print("DB operation: ", statement, args, " deleted from db")