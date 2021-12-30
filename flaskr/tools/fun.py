from flaskr.db import get_db
from mysql.connector import Error
from datetime import datetime

import numpy as np


def get_years(table='produksi'):
    cur = get_db().cursor()

    # ambil tahun dari db
    cur.execute(
        f"SELECT DISTINCT YEAR(periode) FROM {table}"
    )
    years = cur.fetchall() # [(col1), (col2), (col3), ..., (coln)]
    years = np.reshape(years, (-1))
    years.sort() # sorted
    if len(years) == 0:
        years = [0,]
    return years

def get_datas(year=None, table='produksi', dictionary=True):
    cur = get_db().cursor(dictionary=dictionary)

    years = get_years(table)
    
    try:    
        # ambil data berdasarkan tahun
        if year is not None:
            cur.execute(
                f"SELECT id, year(periode) AS years, month(periode) AS months, nilai FROM `{table}` WHERE `periode` LIKE '%s%'",
                (int(year),)
            )
        else:
            cur.execute(
                f"SELECT id, year(periode) AS years, month(periode) AS months, nilai FROM `{table}`"
            )
        return cur.fetchall()
    except ValueError as er:
        return None
    except IndexError as er:
        return None

def generate_id(periode):
    periode_date = datetime.strptime(periode, '%Y-%m-%d')   
    ls_periode = str(periode_date).split('-')

    id = ls_periode[0] + ls_periode[1]
    return id

def insert_datas(datas, table='produksi'):
    db = get_db()
    cur = db.cursor()
    
    error = None
    try:
        id = generate_id(datas[0])
        qwery = f'INSERT INTO {table} (id, periode, nilai) VALUES (%s, %s, %s)'
        
        # return qwery
        cur.execute(qwery, (id, datas[0], datas[1]))
        db.commit()
    except Error as er:
        print(er)
        db.rollback()
        error = str(er)
    except BaseException as er:
        print(f'error: {er}')
        error = str(er)
    except:
        error = 'something error!.'

    print(error)
    return error