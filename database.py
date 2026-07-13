import sqlite3
from sqlite3 import connect
from dataclasses import dataclass, fields
import os
import pandas as pd

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "dreevo.db")
DATA_DIR_PATH = os.path.join(os.path.dirname(__file__), "data")
SQL_QUERY_DIR_PATH = os.path.join(os.path.dirname(__file__), "sql/queries")
SQL_SCHEMA_DIR_PATH = os.path.join(os.path.dirname(__file__), "sql/schema")

def init_db():
    sql_files = ['raw_marketcheck.sql', 'dealers.sql', 'marketplaces.sql', 'listings.sql', 'vehicle_builds.sql']
    for f in sql_files:
        create(f)

def create(sql_file, db_path: str = DB_PATH):
    file_path = os.path.join(SQL_SCHEMA_DIR_PATH, sql_file)
    with open(file_path, 'r') as file:
        query = file.read()
    conn = connect(db_path)
    cursor = conn.cursor()
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        cursor.execute(query)
        conn.commit()
    except sqlite3.Error as error:
        print(f"An error occured: {error}")
    finally:
        conn.close()

def insert_many(objs: list[dataclass], db_path: str = DB_PATH):
    if not objs:
        return []
    conn = connect(db_path)
    cursor = conn.cursor()
    obj = objs[0]
    table = obj.__table__
    _fields = fields(obj)
    column_names = [f.name for f in _fields]
    columns = ", ".join(column_names)
    placeholders = ", ".join(f":{name}" for name in column_names)
    query = f"""
                   INSERT INTO {table} ({columns})
                   VALUES ({placeholders})
        """
    data = [vars(obj) for obj in objs]
    cursor.executemany(query, data)
    conn.commit()
    conn.close()

def insert(obj: dataclass, db_path: str = DB_PATH):
    conn = connect(db_path)
    cursor = conn.cursor()
    table = obj.__table__
    _fields = fields(obj)
    column_names = [f.name for f in _fields]
    columns = ", ".join(column_names)
    placeholders = ", ".join(f":{name}" for name in column_names)
    query = f"""
               INSERT INTO {table} ({columns})
               VALUES ({placeholders})
    """
    cursor.execute(query, vars(obj))
    conn.commit()
    conn.close()

def upsert(objs: list[dataclass], db_path: str = DB_PATH):
    if not objs:
        return []
    conn = connect(db_path)
    cursor = conn.cursor()
    obj = objs[0]
    table = obj.__table__
    _fields = fields(obj)
    column_names = [f.name for f in _fields]
    columns = ", ".join(column_names)
    placeholders = ", ".join(f":{name}" for name in column_names)

    if table == "marketplaces" or table == "dealers":
        conflict_col_names = ["marketcheck_id"]
    else:
        conflict_col_names = ["make", "model", "trim", "version", "year"]
    conflict_cols = ", ".join(conflict_col_names)
    update_set = ", ".join(f"{col} = excluded.{col}" for col in conflict_col_names)
    query = f"""
        INSERT INTO {table} ({columns})
        VALUES ({placeholders})
        ON CONFLICT({conflict_cols}) DO UPDATE SET {update_set}
        RETURNING id;
        """
    ids = []
    for obj in objs:
        cursor.execute(query, vars(obj))
        row = cursor.fetchone()
        if row:
            ids.append(row[0])
    conn.commit()
    conn.close()
    return ids

def query_table(sql_file, db_path: str = DB_PATH):
    file_path = os.path.join(SQL_QUERY_DIR_PATH, sql_file)
    with open(file_path, 'r') as file:
        query = file.read()
    conn = connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        return rows
    except sqlite3.Error as error:
        print(f"An error occured: {error}")
    finally:
        conn.close()

def create_table_from_excel(file, table_name):
    file_path = os.path.join(DATA_DIR_PATH, file)
    df = pd.read_excel(file_path)
    conn = sqlite3.connect(DB_PATH)
    df.to_sql(table_name, conn, if_exists='replace', index=False)
    conn.close()

