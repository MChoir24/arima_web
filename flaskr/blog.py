from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from flask.globals import current_app
from werkzeug.exceptions import abort
from flaskr.auth import login_required
from flaskr.db import get_db
from datetime import date, datetime

bp = Blueprint('blog', __name__)    

@bp.route('/')
def index():
    current_year = datetime.now().year
    cur = get_db().cursor()
    cur.execute(
        "SELECT * FROM `produksi` WHERE `periode` LIKE '%s%'",
        (current_year,)
    )
    productions = cur.fetchall()
    return render_template('blog/index.html', productions=productions)
    
@bp.route('/create', methods=('GET', 'POST'))
@login_required()
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            cur = db.cursor()
            cur.execute(
                'INSERT INTO post (title, body, author_id)'
                ' VALUES (%s, %s, %s)',
                (title, body, g.user[0])
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/create.html')

def get_post(id, check_author=True):
    cur = get_db().cursor()
    cur.execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = %s',
        (id,)
    )
    post = cur.fetchone()
    if post is None:
        abort(404, "Post id {0} doesn't exist.".format(id))

    if check_author and post[4] != g.user[0]:
        abort(403)

    return post

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required()
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            cur = db.cursor()
            cur.execute(
                'UPDATE post SET title = %s, body = %s'
                ' WHERE id = %s',
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/update.html', post=post)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required()
def delete(id):
    get_post(id)
    db = get_db()
    cur = db.cursor()
    cur.execute('DELETE FROM post WHERE id = %s', (id,))
    db.commit()
    return redirect(url_for('blog.index'))

@bp.route('/coba')
@login_required(user_types=['admin'])
def coba():
    return 'cobabba'