import functools
from os import error

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash
from flaskr.db import get_db
from flaskr.admin import create_user

def login_required(user_types=['user']):
    def decor(view):
        @functools.wraps(view)
        def wrapped_view(**kwargs):
            session['request_url'] = request.url
            # print(request.url)
            if g.user is None:
                return redirect(url_for('auth.login'))
            elif g.user['type'] not in user_types:
                return redirect(url_for('blog.index'))
            return view(**kwargs)
        return wrapped_view
    return decor


bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=('GET', 'POST'))
@login_required(user_types=['admin'])
def register():
    """
    register
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        lvl = 0
        error = create_user(username, password, str(lvl))
        
        if error is None:
            return redirect(url_for('auth.login'))
        else:
            flash(error)
    
    return render_template('auth/register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    """
    login
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cur = get_db().cursor()
        error = None
        cur.execute(
            'SELECT * FROM user WHERE username = %s', (username,)
        )
        user = cur.fetchone()
        # print('user =======', user)
        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user[2], password):
            error = 'Incorrect password.'

        if error is None:
            request_url = session.get('request_url', None)
            print('cobbaa= ',request_url)
            session.clear()
            session['user_id'] = user[0]
            if request_url:
                return redirect(request_url)
            else:
                return redirect(url_for('index'))

        flash(error)
        return render_template('auth/login.html')
    elif request.method == 'GET':
        if g.user is None:
            return render_template('auth/login.html')
        else:
            return redirect(url_for('index'))

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        cur = get_db().cursor()
        cur.execute(
            'SELECT user.id, user.username, user_type.type_name'
            ' FROM `user` INNER JOIN user_type '
            ' ON user.id_type=user_type.id_type'
            ' WHERE user.id=%s', 
            (user_id,)
        )
        temp = cur.fetchone()
        g.user = {}
        g.user['id'] = temp[0]
        g.user['name'] = temp[1]
        g.user['type'] = temp[2]
