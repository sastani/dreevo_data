import sqlite3
from sqlite3 import connect
from dataclasses import dataclass, fields
import os
import pandas as pd

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "dreevo.db")
DATA_DIR_PATH = os.path.join(os.path.dirname(__file__), "data")

def init_db(db_path: str = DB_PATH):
    conn = connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS raw_marketcheck(
            marketcheck_id TEXT UNIQUE,
            fetched_at     TEXT,
            api_endpoint   TEXT,
            listing_type   TEXT,
            query_params   TEXT,
            listing_json   TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS dealers(
            id          INTEGER PRIMARY KEY,
            marketcheck_id INT UNIQUE,
            name        TEXT,
            dealer_type TEXT,
            dealership_group_name TEXT,
            website     TEXT,
            street      TEXT,
            city        TEXT,
            state       TEXT,
            country     TEXT,
            zip         TEXT,
            phone       TEXT,
            contact_email TEXT
        );
        
        CREATE TABLE IF NOT EXISTS marketplaces(
            id          INTEGER PRIMARY KEY,
            marketcheck_id INT UNIQUE,
            name          TEXT,
            website       TEXT UNIQUE NOT NULL
        );

        CREATE TABLE IF NOT EXISTS listings(
            id                   INTEGER PRIMARY KEY,
            marketcheck_id       TEXT UNIQUE,
            year                 INTEGER,
            make                 TEXT,
            model                TEXT,
            trim                 TEXT,
            version              TEXT,
            vin                  TEXT,
            heading              TEXT,
            seller_name          TEXT,
            city                 TEXT,
            state                TEXT,
            zip                  INT, 
            region               TEXT,  
            price                REAL,
            buy_now_price        REAL, -- NULL if a dealer or private party listing
            mileage              INTEGER,
            msrp                 REAL,
            listing_url          TEXT,
            carfax_1_owner       INTEGER,
            carfax_clean_title   INTEGER,
            exterior_color       TEXT,
            interior_color       TEXT,
            base_exterior_color       TEXT,
            base_interior_color       TEXT,
            days_on_market        INTEGER, -- total days on market since first seen
            days_on_market_180    INTEGER, -- days active within the last 180-day window
            days_on_market_active INTEGER, -- days continuously active in current listing period across all channels
            days_on_site_active   INTEGER, -- days active on the dealer's own website
            listing_type          TEXT,
            inventory_type       TEXT,
            stock_num            TEXT,
            scraped_at_date      TEXT,
            in_transit           BOOLEAN,
            vehicle_status       TEXT,
            reference_price      REAL,
            reference_price_date INTEGER,
            price_change_percent REAL,
            reference_miles      INTEGER,
            reference_miles_date INTEGER,
            source               TEXT,
            dealer_id            INTEGER REFERENCES dealers(id),
            marketplace_id       INTEGER REFERENCES marketplaces(id),
            vehicle_build_id     INTEGER REFERENCES vehicle_builds(id)
        );

        CREATE TABLE IF NOT EXISTS vehicle_builds(
            id                   INTEGER PRIMARY KEY,
            year                 INTEGER,
            make                 TEXT,
            model                TEXT,
            trim                 TEXT,
            version              TEXT,
            body_type            TEXT,
            transmission         TEXT,
            drivetrain           TEXT,
            fuel_type            TEXT,
            engine               TEXT,
            engine_size          INTEGER,
            engine_block         TEXT,
            doors                INTEGER,
            cylinders            INTEGER,
            made_in              TEXT,
            highway_mpg          INTEGER,
            city_mpg             INTEGER,
            powertrain_type      TEXT,
            UNIQUE(
                make,
                model,
                trim,
                version,
                year
            )
        );
    """)
    conn.commit()
    conn.close()

def insert(objs: list[dataclass], db_path: str = DB_PATH):
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

    if table == "marketplaces" or table == "raw_marketcheck" or table == "listings" or table == "dealers":
        conflict_col_names = ["marketcheck_id"]
    else:
        conflict_col_names = ["make", "model", "trim", "version", "year"]
    conflict_cols = ", ".join(conflict_col_names)
    update_set = ", ".join(f"{col} = excluded.{col}" for col in conflict_col_names)
    if table == "raw_marketcheck":
        query = f"""
            INSERT INTO {table} ({columns})
            VALUES ({placeholders})
            ON CONFLICT({conflict_cols}) DO UPDATE SET {update_set}
        """
    else:
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

def create_table_from_excel(file, table_name):
    file_path = os.path.join(DATA_DIR_PATH, file)
    df = pd.read_excel(file_path)
    conn = sqlite3.connect(DB_PATH)
    df.to_sql(table_name, conn, if_exists='replace', index=False)
    conn.close()