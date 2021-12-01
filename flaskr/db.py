import click
import mysql.connector
# from click.termui import clear
from flask.cli import with_appcontext
# from flaskext.mysql import MySQL
from flask import current_app, g
from werkzeug.security import generate_password_hash


def get_db():
    """
    get database
    """
    if 'db' not in g:
        mydb = mysql.connector.connect(
                            host="localhost",
                            port=6033,
                            user="root",
                            password="root",
                            database="arima",
                        )

        g.db = mydb

    return g.db

def close_db(e=None):
    """
    close database
    """
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """
    initialitation databese
    """
    db = get_db()
    cur = db.cursor()

    executeScriptsFromFile(cur, "schema2.sql")

    cur.execute(
            "INSERT INTO user (username, password, id_type) VALUES (%s, %s, %s)",
            ('admin', generate_password_hash('admin'), 1)
        )
    db.commit()

    # with current_app.open_resource('schema.sql') as f:
    #     db.executescript(f.read().decode('utf8'))

def executeScriptsFromFile(cursor, filename):
    fd = current_app.open_resource(filename)
    sqlFile = fd.read().decode('utf8')
    fd.close()
    sqlFile = sqlFile.replace("\n", "")
    sqlCommands = sqlFile.split(';')
    for command in sqlCommands:
        try:
            if command.strip() != '':
                cursor.execute(command)
        except IOError as msg:
            print("Command skipped: ", msg)

@click.command('init-db')
@with_appcontext    
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)