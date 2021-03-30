import click
import os
import pymysql
import mysql.connector
# from click.termui import clear
from flask.cli import with_appcontext
# from flaskext.mysql import MySQL
from flask import current_app, g


def get_db():
    """
    get database
    """
    if 'db' not in g:
        # current_app.config['MYSQL_DATABASE_HOST'] = "127.0.0.1"
        # current_app.config['MYSQL_DATABASE_PORT'] = 6033
        # current_app.config['MYSQL_DATABASE_USER'] = "root"
        # current_app.config['MYSQL_DATABASE_PASSWORD'] = "root"
        # current_app.config['MYSQL_DATABASE_DB'] = "arima"

        # mysql = MySQL()
        # print(current_app)
        # mysql.init_app(current_app.config['DATABASE'])

        # mysql = MySQL(
        #     current_app.config['DATABASE'], 
        #     prefix='mysql', 
        #     host=os.getenv("localhost"), 
        #     port=6033,
        #     user=os.getenv("root"),
        #     password=os.getenv("root"),
        #     db=os.getenv("arima"), 
        #     autocommit=True, 
        #     cursorclass=pymysql.cursors.DictCursor
        # )

        mydb = mysql.connector.connect(
                            host="localhost",
                            port=6033,
                            user="root",
                            password="root",
                            database="arima"
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

    executeScriptsFromFile(db.cursor(), "schema.sql")
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