from flask import (
    Blueprint, flash, g, json, redirect, render_template, request, url_for, jsonify, send_file
)
from flask.globals import current_app
from flaskr.auth import login_required
from flaskr.db import get_db
from flaskr.tools.arima import perkiraan_arima
from flaskr.tools.fun import get_years, get_datas, generate_id, insert_datas
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from mysql.connector import Error

import os
import numpy as np
import pandas as pd



CURRENT_YEAR = datetime.now().year


# routes
bp = Blueprint('blog', __name__)

# ''' Dashboard '''
@bp.route('/')
@login_required(user_types=['user', 'admin'])
def index():
    years = get_years()

    cur_year = request.args.get('year', CURRENT_YEAR)
    
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

    cur_year = request.args.get('year', CURRENT_YEAR)
    productions = get_datas(cur_year)
    peramalan = get_datas(cur_year, table='hasil_peramalan')
    if not productions and not peramalan:
        abort(404, f"Kata kunci {cur_year} tidak cocok!.")

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
@login_required(user_types=['user', 'admin'])
def hapus_data():
    pass


# ''' Data Garam '''
@bp.route('/datagaram')
@login_required(user_types=['user', 'admin'])
def data_garam():
    years = get_years()

    cur_year = request.args.get('year', CURRENT_YEAR)

    productions = get_datas(year=cur_year)
    if productions is None:
        abort(404, f"Maaf, kata kunci {cur_year} tidak cocok!.")

    return render_template('blog/data_garam.html', 
        productions=productions, 
        years=years, 
        cur_year=cur_year
        )

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
        "SELECT id, username, id_type FROM user"
    )
    users = cur.fetchall()
    
    return render_template(
        'blog/users.html',
        users=users
    )


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required()
def delete(id):
    get_post(id)
    db = get_db()
    cur = db.cursor()
    cur.execute('DELETE FROM post WHERE id = %s', (id,))
    db.commit()
    return redirect(url_for('blog.index'))

@bp.errorhandler(404)
def not_found(e):
    years = get_years()
    return render_template('errors/404.html', years=years), 404

@bp.route('/coba')
@login_required(user_types=['admin'])
def coba():
    return 'cobabba'