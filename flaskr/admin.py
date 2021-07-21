import click

from flask.cli import with_appcontext
from flaskr.db import get_db, close_db
from werkzeug.security import generate_password_hash

# create new user
@click.command('create-user')
@click.option('--name', help='username')
@click.option('--password', help='password')
@click.option('--lvl', help='user level 0=general users, 1=admin users')
@with_appcontext    
def create_user(name, password, lvl):
    print('name ', name)
    print('password ', password)
    print('lvl ', lvl)
    lvl = int(lvl)
    db = get_db()
    cur = db.cursor()
    error = None
    cur.execute(
            'SELECT id FROM user WHERE username = %s', (name,)
        )
    if cur.fetchone() is not None:
        error = f'User {name} is already registered.'

    if error is None:
        cur.execute(
            "INSERT INTO user (username, password, id_type) VALUES (%s, %s, %s)",
            (name, generate_password_hash(password), lvl)
        )
        db.commit()
    click.echo(f'Error = {error}')
    return error

def init_app(app):
    # app.teardown_appcontext(close_db)
    app.cli.add_command(create_user)