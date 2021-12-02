from flask import (
    Blueprint, flash, g, json, redirect, render_template, request, url_for, jsonify, send_file
)
from .tools.arima import perkiraan_arima
from .tools.fun import get_years, get_datas, generate_id, insert_datas
from flask.globals import current_app
from flaskr.auth import login, login_required
from flaskr.db import get_db
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from mysql.connector import Error


import os
import numpy as np
import pandas as pd


# routes
bp = Blueprint('blog', __name__)


# get_years()[-1] = get_years()[-1]

# ''' Dashboard '''
@bp.route('/')
@login_required(user_types=['user', 'admin'])
def index():
    years = get_years()

    cur_year = request.args.get('year', get_years()[-1])
    
    productions = get_datas(year=cur_year)
    if not productions:
        abort(404, f"Maaf, kata kunci {cur_year} tidak cocok!.")

    return render_template('blog/index.html', 
        productions=productions, 
        years=years, 
        cur_year=cur_year
        )

# ''' Peramalan '''

def insert_peramalan(periode): # insert data peramalan ke database
    list_periode = periode.split('-')
    year = int(list_periode[0])
    month = int(list_periode[1])
    print('============', year)
    print('============', month)

    productions = get_datas(year, table='produksi')
    print(productions)
    nilai = 0
    if month > 4: # mulai meramal pada bulan 5 (mei)
        print('len produksi, ', len(productions))
        nilai_real = productions[-1]['nilai']
        nilai = np.random.normal(loc=nilai_real)

    insert_datas((periode, nilai), table='hasil_peramalan')

@bp.route('/peramalan', methods=('GET', 'POST'))
@login_required(user_types=['user', 'admin'])
def peramalan():
    years = get_years()
    disabled_tambah_tahun = 'true'
    is_last_year = False

    if request.method == 'POST': # tambah data per bulan
        periode = request.form['periode']
        nilai = request.form['nilai']
        
        db = get_db()
        cur = db.cursor()
        try:
            id = generate_id(periode)
            qwery = 'INSERT INTO produksi (id, periode, nilai) VALUES (%s, %s, %s)'
            
            cur.execute(qwery, (id, periode, nilai))
            db.commit()
            # return 'success'
        except Error as er:
            print(er)
            db.rollback()
            return f'None, {er}'
        except BaseException as er:
            print(f'something erclose_dbror: {er}')
            return str(er)
        
        date_obj = datetime.strptime(periode, '%Y-%m-%d')
        next_periode = (date_obj + relativedelta(months=1)).date()
        insert_peramalan(str(next_periode))

        return redirect(url_for('blog.peramalan', year=years[-1]))

    cur_year = request.args.get('year', get_years()[-1])
    productions = get_datas(cur_year)
    peramalan = get_datas(cur_year, table='hasil_peramalan')
    if not productions and not peramalan:
        abort(404, f"Kata kunci {cur_year} tidak cocok!.")
    if not peramalan:
        peramalan = np.zeros((12))

    if len(get_datas(years[-1])) == 12:
        disabled_tambah_tahun = 'false'
    
    if int(cur_year) == years[-1]:
        is_last_year = True

    return render_template('blog/peramalan.html',
        productions=productions,
        peramalan=peramalan,
        years=years,
        cur_year=cur_year,
        disabled_tambah_tahun = disabled_tambah_tahun,
        is_last_year=is_last_year
    )

@bp.route('/tambah-tahun')
@login_required(user_types=['user', 'admin'])
def tambah_tahun():
    years = get_years()

    if len(get_datas(years[-1])) < 12:
        abort(400, f"Mohon lengkapi data tahun {years[-1]}!.")

    peramalan = get_datas(years[-1]+1, table='hasil_peramalan')
    if not peramalan:
        periode = str(date(years[-1]+1, 1, 1))
        inserted = insert_datas((periode, 0), table='hasil_peramalan')

    return redirect(url_for('blog.peramalan', year=years[-1] + 1))

@bp.route('/hapus-data')
@login_required(user_types=['user'])
def hapus_data():
    periode = request.args.get('periode', 0)
    id_periode = generate_id(periode)

    date_obj = datetime.strptime(periode, '%Y-%m-%d')
    year = date_obj.year
    next_periode = (date_obj + relativedelta(months=1)).date()
    id_peramalan = generate_id(str(next_periode))
    # return f'{periode} -> {str(next_periode)}'


    last_year = get_years(table='produksi')[-1]
    last_data = get_datas(last_year, table='produksi')[-1]

    if int(id_periode) != last_data['id']: # delete data when id from request is equal with last id from db
        abort(403)

    db = get_db()
    cur = db.cursor()
    try:
        cur.execute('DELETE FROM produksi WHERE id = %s', (id_periode,))
        cur.execute('DELETE FROM hasil_peramalan WHERE id = %s', (id_peramalan,))
        db.commit()
    except Error as er:
        print(er)
        db.rollback()
        return f'None, {er}'
    except BaseException as er:
        print(f'something erclose_dbror: {er}')
        return str(er)
    
    return redirect(url_for('blog.peramalan', year=year))
    # return 'sama'


# ''' Data Garam '''
@bp.route('/datagaram')
@login_required(user_types=['user', 'admin'])
def data_garam():
    years = get_years()

    cur_year = request.args.get('year', get_years()[-1])

    productions = get_datas(year=cur_year)
    if productions is None:
        abort(404, f"Maaf, kata kunci {cur_year} tidak cocok!.")

    return render_template('blog/data_garam.html', 
        productions=productions, 
        years=years, 
        cur_year=cur_year
        )

@bp.route('/hapus-data-tahun')
@login_required(user_types=['user', 'admin'])
def hapus_data_tahun():
    year_produksi = int(request.args.get('year', 0))
    
    # validasi
    last_year = get_years(table='produksi')[-1]
    if year_produksi != last_year:
        abort(403)
    
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute("DELETE FROM produksi WHERE WHERE `periode` LIKE '%s%';", (year_produksi,))
        cur.execute("DELETE FROM hasil_peramalan WHERE `periode` LIKE '%s%';", (year_produksi,))
        cur.execute("DELETE FROM hasil_peramalan WHERE `periode` LIKE '%s%';", (year_produksi+1),)

        db.commit()
    except Error as er:
        print(er)
        db.rollback()
        return f'None, {er}'
    except BaseException as er:
        print(f'something erclose_dbror: {er}')
        return str(er)

    periode = f'{year_produksi}-01-01'
    insert_datas((periode, 0), table='hasil_peramalan')

    return redirect(url_for('blog.peramalan', year=year_produksi))



@bp.route('/create', methods=('GET', 'POST'))
@login_required(user_types=['user', 'admin'])
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error, 'danger')
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


@bp.route('/<int:year>/update', methods=('GET', 'POST'))
@login_required(user_types=['admin', 'user'])
def data_garam_update(year):
    productions = get_datas(year=year)
    cur = get_db().cursor()

    if productions is None:
        abort(404, f"Maaf, kata kunci {year} tidak cocok!.")

    if request.method == 'POST':
        # return jsonify(len(request.form))
        form = request.form
        for i in range(1, (len(form)//4) + 1):
            id = request.form[f'id{i}']
            month = request.form[f'month{i}']
            year = request.form[f'year{i}']
            nilai = request.form[f'nilai{i}']
            error = None
            
            # validasi form
            if not (month != '' and year != '' and nilai != ''):
                error = 'Masukan harus terisi semua.'
            else:
                try:
                    month, year, nilai = int(month), int(year), float(nilai)
                except ValueError:
                    error = 'Masukan harus berupa angka'
            
            if error is not None: # Tempilkan Error
                print(error)
                flash(error, 'danger')
                return render_template('blog/update_produksi.html', productions=productions)
            else: # Jika tidak ada error
                db = get_db()
                cur = db.cursor()

                date = f"{year}-{month}-1"
                try:
                    cur.execute(
                        'UPDATE produksi SET periode = %s, nilai = %s'
                        ' WHERE id = %s',
                        (date, nilai, id)
                    )
                    db.commit()
                except Error as er:
                    print(er)
                    db.rollback()
                    error = f'Terjadi kesalahan saat mengubah data.'
                    flash(error, 'danger')
                    return render_template('blog/update_produksi.html', productions=productions)

        return redirect(url_for('blog.data_garam', year=year))

    return render_template('blog/update_produksi.html', productions=productions, year=year)


UPLOAD_FOLDER = os.path.join('flaskr','uploads','datas')
ALLOWED_EXTENSIONS = {'csv', }

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/import-data', methods=('GET', 'POST'))
@login_required(user_types=['admin', 'user'])
def import_data():
    if request.method == 'POST':
        # upload to server
        error = None
        # return jsonify(request.files)
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('File csv belum dipilih!', 'danger')
            return redirect(request.url)

        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            error = 'File tidak valid!'

        elif not allowed_file(file.filename):
            error = 'Format file harus berupa *.csv'
            
        # tampilkan error jika ada error
        if error:
            flash(error, 'danger')
            return redirect(request.url)
        # jika tidak ada error mulai operasi import 
        else:
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename); 
            filepath_new = os.path.join(UPLOAD_FOLDER, 'data.csv'); 
            file.save(filepath)
            os.remove(filepath_new) if os.path.exists(filepath_new) else None # remove file if data.csv si already exist
            os.rename(filepath, os.path.join(UPLOAD_FOLDER, 'data.csv'))
        
            filename = filepath_new
            datas = pd.read_csv(filename, index_col=False, delimiter=';')

            # validasi tahun yang sudah ada.
            tahun_data = int(datas.values[0, 0][:4])
            if tahun_data in get_years():
                flash('Tahun sudah ada!', 'danger')
                return redirect(request.url)

            for i, data_row in datas.iterrows():
                datas = (data_row[0], data_row[1])
                inserted = insert_datas(datas, table='produksi')
                print(inserted)
                
            flash(f'Berhasil import data tahun {tahun_data}!', 'success')
            return redirect(url_for('blog.data_garam', year=tahun_data))

    return render_template('blog/import_data.html')

@bp.route('/download-contoh-csv')
@login_required(user_types=['admin', 'user'])
def download_file():
    path = './static/csv/data.csv'
    return send_file(path, as_attachment=True)

# ''' Kelola User (Admin saja) '''
@bp.route('/users')
@login_required(user_types=['admin'])
def users():
    cur = get_db().cursor(dictionary=True)
    cur.execute(
        "SELECT id, user.username, user.id_type, user_type.type_name FROM user INNER JOIN user_type ON user.id_type = user_type.id_type"
    )
    users = cur.fetchall()
    # return jsonify(users)
    return render_template(
        'blog/users.html',
        users=users
    )

@bp.route('/users/add-user', methods=('GET', 'POST'))
@login_required(user_types=['admin'])
def add_user():
    db = get_db()
    cur = db.cursor(dictionary=True)

    if request.method == 'POST':
        # get request
        username = request.form['username']
        password = request.form['password']
        id_type = request.form['id_type']

        cur = db.cursor()

        # get all users for validation
        cur.execute("select * from user where username=%s", (username,))
        users = cur.fetchone()

        # validations
        if username == '' or password == '':
            flash("Isian tidak boleh kosong", "danger")
            return redirect(url_for('blog.add_user'))

        if users:
            if username in users:
                flash("Username sudah tersedia.", "danger")
                return redirect(url_for('blog.add_user'))
                

        try:
            cur.execute(
                "insert into user (username, password, id_type) values (%s, %s, %s)",
                (username, generate_password_hash(password), id_type)
            )
            db.commit()
        except Error as er:
            print(er)
            db.rollback()
            error = f'Terjadi kesalahan saat menambah data.'
            flash(error, 'danger')
            return redirect(url_for('blog.users'))
        
        return redirect(url_for('blog.users'))

    # get all type
    cur.execute('select * from user_type where 1')
    user_type = cur.fetchall()

    return render_template(
        'blog/add_user.html',
        user_type = user_type
        )

@bp.route('/users/<id>', methods=('GET', 'POST'))
@login_required(user_types=['admin'])
def edit_user(id):
    # if METHOD POST
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute(
        "SELECT id, username, id_type FROM user WHERE id = %s",
        (id,)
    )
    user = cur.fetchone()

    if request.method == 'POST':
        # get request
        id = request.form['id']
        username = request.form['username']
        id_type = request.form['id_type']

        # get all users
        # cur.execute('SELECT * FROM user WHERE 1')
        # users = cur.fetchone()
        # return jsonify(users)

        # # validation
        # if username != user['username']:
        #     if username in users:
        #         flash("Username telah digunakan", 'danger')
        #         return redirect(url_for('blog.edit_user', user=user))
        try:
            # return jsonify([id, username, id_type])
            cur = db.cursor()
            cur.execute(
                        "UPDATE user SET username = %s, id_type = %s WHERE id = %s",
                        (username, id_type, id)
                    )
            db.commit()
        except Error as er:
            print(er)
            db.rollback()
            error = f'Terjadi kesalahan saat mengubah data.'
            flash(error, 'danger')
            return redirect(url_for('blog.users'))

        return redirect(url_for('blog.users'))
    # METHOD GET

    cur.execute(
        "SELECT * FROM user_type WHERE 1"
    )
    user_type = cur.fetchall()
    # return jsonify(user)
    return render_template(
        'blog/edit_user.html',
        user = user,
        user_type = user_type
    )

@bp.route('/users/<id>/change-passwd', methods=['GET', 'POST'])
@login_required(user_types=['admin'])
def ubah_password(id):
    db = get_db()
    cur = db.cursor()

    if request.method == 'POST':
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # validation
        if password == '':
            flash('Isian harus diisi', 'danger')
            return redirect(url_for('blog.ubah_password', id=id))

        if password != confirm_password:
            flash('Ulangi password.!', 'danger')
            return redirect(url_for('blog.ubah_password', id=id))

        try:
            cur = db.cursor()
            cur.execute(
                        "UPDATE user SET password = %s WHERE id = %s",
                        (generate_password_hash(password), id)
                    )
            db.commit()
        except Error as er:
            print(er)
            db.rollback()
            error = f'Terjadi kesalahan saat mengubah data.'
            flash(error, 'danger')
            return redirect(url_for('blog.users'))

        return redirect(url_for('blog.users'))

    return render_template('blog/ubah_password.html', id=id)

@bp.route('/user/<id>/delete')
@login_required(user_types=['admin'])
def hapus_user(id):
    db = get_db()
    cur = db.cursor(dictionary=True)

    # validasi jika user admin <= 1 tidak dapat dihapus
    cur.execute(
        'SELECT id, user.id_type FROM user WHERE id = %s',
        (id, )
    )
    user = cur.fetchone()
    
    cur.execute(
        'SELECT id, user.username, user.id_type, user_type.type_name FROM user_type INNER JOIN user ON user_type.id_type = user.id_type where user_type.id_type = %s',
        (user['id_type'],)
        )
    users = cur.fetchall()
    # return jsonify(type(user['id_type']))
    # print('-------------', type(user['id_type']))
    if (len(users) < 2 and user['id_type'] == 1) or user['id'] == g.user['id']:
        flash('tidak dapat menghapus user yang dipilih.', 'danger')
        return redirect(url_for('blog.users'))

    try:
        cur.execute('DELETE FROM user WHERE id = %s', (id,))
        db.commit()
    except Error as er:
        print(er)
        db.rollback()
        return f'None, {er}'
    except BaseException as er:
        print(f'something erclose_dbror: {er}')
        return str(er)

    return redirect(url_for('blog.users'))


# @bp.route('/<int:id>/delete', methods=('POST',))
# @login_required()
# def delete(id):
#     get_post(id)
#     db = get_db()
#     cur = db.cursor()
#     cur.execute('DELETE FROM post WHERE id = %s', (id,))
#     db.commit()
#     return redirect(url_for('blog.index'))

@bp.errorhandler(404)
def not_found(e):
    years = get_years()
    return render_template('errors/404.html', years=years), 404

@bp.route('/coba')
@login_required(user_types=['admin'])
def coba():
    return 'cobabba'
