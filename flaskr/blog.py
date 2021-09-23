from logging import error
from flask import (
    Blueprint, flash, g, json, redirect, render_template, request, url_for, jsonify, send_file
)
from flask.globals import current_app
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename
from flaskr.auth import login_required
from flaskr.db import get_db
from datetime import datetime
from mysql.connector import Error

import os
import numpy as np
import pandas as pd

CURRENT_YEAR = datetime.now().year

def get_years():
    cur = get_db().cursor()

    # ambil tahun dari db
    cur.execute(
        "SELECT DISTINCT YEAR(periode) FROM produksi"
    )
    years = cur.fetchall() # [(col1), (col2), (col3), ..., (coln)]
    years = np.reshape(years, (-1))
    years.sort() # sorted
    return years

def get_productions(year):
    cur = get_db().cursor(dictionary=True)
    
    try:    
        # ambil data berdasarkan tahun
        cur.execute(
            "SELECT id, year(periode) AS years, month(periode) AS months, nilai FROM `produksi` WHERE `periode` LIKE '%s%'",
            (int(year),)
        )
        return cur.fetchall()
    except ValueError as er:
        return None


# routes
bp = Blueprint('blog', __name__)

@bp.route('/')
@login_required(user_types=['user', 'admin'])
def index():
    years = get_years()

    cur_year = request.args.get('year', CURRENT_YEAR)
    
    productions = get_productions(year=cur_year)
    if productions is None:
        abort(404, f"Maaf, kata kunci {cur_year} tidak cocok!.")

    return render_template('blog/index.html', 
        productions=productions, 
        years=years, 
        cur_year=cur_year
        )

@bp.route('/datagaram')
@login_required(user_types=['user', 'admin'])
def data_garam():
    years = get_years()

    cur_year = request.args.get('year', CURRENT_YEAR)

    productions = get_productions(year=cur_year)
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
    productions = get_productions(year=year)
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


UPLOAD_FOLDER = 'flaskr/uploads/datas'
ALLOWED_EXTENSIONS = {'csv', }

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/import-data', methods=('GET', 'POST'))
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
        
            # import to db
            db = get_db()
            cur = db.cursor()
            filename = filepath_new
            datas = pd.read_csv(filename, index_col=False, delimiter=';')

            # validasi tahun yang sudah ada.
            tahun_data = int(datas.values[0, 0][:4])
            if tahun_data in get_years():
                flash('Tahun sudah ada!', 'danger')
                return redirect(request.url)

            for i, data_row in datas.iterrows():
                try:
                    print(str(data_row))
                    qwery = 'INSERT INTO produksi (periode, nilai) VALUES (%s, %s)'
                    print(qwery)
                    # return qwery
                    cur.execute(qwery, tuple(data_row))
                    db.commit()
                    # return 'success'
                except Error as er:
                    print(er)
                    db.rollback()
                    return f'None, {er}'
                except BaseException as er:
                    print(f'something erclose_dbror: {er}')
                    return str(er)
                
                except:
                    return redirect('/')
            flash(f'Berhasil import data tahun {tahun_data}!', 'success')
            return redirect(url_for('blog.data_garam', year=tahun_data))

    return render_template('blog/import_data.html')

@bp.route('/download-contoh-csv')
def download_file():
    path = './static/csv/data.csv'
    return send_file(path, as_attachment=True)

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