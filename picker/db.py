import sqlite3
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

class CollHandler():
    def __init__(self):
        self.insert_statement = "INSERT INTO collections (title, facetedTitle) VALUES (?, ?)"
        self.read_all_statement = "SELECT * FROM collections"
        self.read_one_statement = "SELECT * FROM collections WHERE facetedTitle = ?"
        self.update_one_statement = "UPDATE collections SET title = ?, facetedTitle = ? WHERE id = ?"

    def write_new(self, data):
        db = get_db()
        cursor = db.cursor()
        error = None

        try:
            cursor.execute(self.insert_statement, (data["title"], data["facetedTitle"]))
            db.commit()
            return ("{} saved to DB".format(data["title"]))
        except db.IntegrityError:
            error = "Collection already in DB"

    def get_all(self):
        db = get_db()

        read_data = db.execute(self.read_all_statement).fetchall()

        return read_data

    def get_coll(self, facetedTitle):
        db = get_db()
        coll_data = db.execute(self.read_one_statement, (facetedTitle,)).fetchone()

        return coll_data

    def delete_one(self, id_value):
        db = get_db()
        db.execute("DELETE FROM collections WHERE facetedTitle = ?", (id_value,))
        db.commit()

class RecordHandler():
    def __init__(self):
        self.insert_statement = "INSERT INTO records (irn, title, type, collectionId, identifier, dateLabel, dateValue, personLabel, qualityScore, include) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        self.read_all_statement = "SELECT * FROM records"
        self.read_one_statement = "SELECT * FROM records WHERE irn = ?"
        self.update_one_statement = "UPDATE records SET include = ? WHERE irn = ?"

    def write_new(self, data):
        db = get_db()
        cursor = db.cursor()

        try:
            cursor.execute(self.insert_statement, (data["irn"], data["title"], data["type_val"], data["collectionId"], data["identifier"], data["dateLabel"], data["dateValue"], data["personLabel"], data["qualityScore"], data["include"]))
            db.commit()
            return ("{} saved to DB".format(data["title"]))
        except db.IntegrityError:
            error = "Record already in DB"

    def get_all(self):
        db = get_db()

        read_data = db.execute(self.read_all_statement).fetchall()

        return read_data

    def query_recs(self, statement, value):
        db = get_db()

        read_data = db.execute(statement, (int(value),)).fetchall()

        return read_data

    def get_rec(self, irn):
        db = get_db()
        rec_data = db.execute(self.read_one_statement, (irn,)).fetchone()

        return rec_data

    def update_rec(self, data):
        db = get_db()
        try:
            db.execute(self.update_one_statement, (data["include"], data["db_id"]))
            db.commit()
            return "{} was successfully updated".format(data["irn"])
        except:
            return None

    def delete_one(self, id_value):
        db = get_db()
        db.execute("DELETE FROM records WHERE irn = ?", (id_value,))
        db.commit()

class MediaHandler():
    def __init__(self):
        self.insert_statement = "INSERT INTO media (irn, recordId, type, width, height, license, include) VALUES (?, ?, ? , ?, ?, ?, ?)"
        self.read_all_statement = "SELECT * FROM media"
        self.read_one_statement = "SELECT * FROM media WHERE id = ?"
        self.update_one_statement = "UPDATE media SET include = ? WHERE irn = ?"

    def write_new(self, data):
        db = get_db()
        cursor = db.cursor()

        try:
            cursor.execute(self.insert_statement, (data["media_irn"], data["recordId"], data["type_val"], data["width"], data["height"], data["license"], data["include"]))
            db.commit()
            return ("{} saved to DB".format(data["media_irn"]))
        except db.IntegrityError:
            error = "Media already in DB"

    def get_all(self):
        db = get_db()

        read_data = db.execute(self.read_all_statement).fetchall()

        return read_data

    def get_med(self, statement, value, one=False):
        db = get_db()
        if one == True:
            med_data = db.execute(statement, (value,)).fetchone()
        else:
            med_data = db.execute(statement, value).fetchall()
        return med_data

    def update_med(self, irn, selection):
        db = get_db()

        try:
            db.execute(self.update_one_statement, (selection, irn))
            db.commit()
            return "{} was successfully updated".format(irn)
        except:
            return None

    def delete_one(self, id_value):
        db = get_db()
        db.execute("DELETE FROM media WHERE irn = ?", (id_value,))
        db.commit()

class PeopleHandler():
    def __init__(self):
        self.insert_statement = "INSERT INTO people (title, irn, recordId) VALUES (?, ?, ?)"
        self.read_all_statement = "SELECT * FROM people"
        self.read_one_statement = "SELECT * FROM people WHERE irn = ?"
        self.update_one_statement = "UPDATE people SET title = ?, irn = ? WHERE id = ?"

    def write_new(self, data):
        db = get_db()
        cursor = db.cursor()

        try:
            cursor.execute(self.insert_statement, (data["title"], data["irn"], data["recordId"]))
            db.commit()
            return ("{} saved to DB".format(data["title"]))
        except db.IntegrityError:
            error = "Person already in DB"

    def get_all(self):
        db = get_db()

        read_data = db.execute(self.read_all_statement).fetchall()

        return read_data

    def get_per(self, irn):
        db = get_db()
        per_data = db.execute(self.read_one_statement, (irn,)).fetchone()

        return per_data

    def delete_one(self, id_value):
        db = get_db()
        conn.execute("DELETE FROM people WHERE irn = ?", (id_value,))
        db.commit()