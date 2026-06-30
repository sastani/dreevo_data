from sqlite3 import connect
from dataclasses import dataclass, fields

def init_db(db_path: str = "dreevo.db"):
    conn = connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS dealers (
            id          INTEGER PRIMARY KEY,
            marketcheck_id TEXT UNIQUE,
            name        TEXT,
            dealer_type TEXT,
            website     TEXT,
            street      TEXT,
            city        TEXT,
            state       TEXT,
            country     TEXT,
            zip         TEXT,
            phone       TEXT,
            contact_email TEXT
        );

        CREATE TABLE IF NOT EXISTS listings (
            id                   INTEGER PRIMARY KEY,
            marketcheck_id       TEXT UNIQUE,
            year                 INTEGER,
            make                 TEXT,
            model                TEXT,
            trim                 TEXT,
            version              TEXT,
            vin                  TEXT,
            heading              TEXT,
            price                REAL,
            mileage              INTEGER,
            msrp                 REAL,
            listing_url          TEXT,
            carfax_1_owner       INTEGER,
            carfax_clean_title   INTEGER,
            exterior_color       TEXT,
            interior_color       TEXT,
            base_ext_color       TEXT,
            base_int_color       TEXT,
            days_on_market        INTEGER, -- total days on market since first seen
            days_on_market_180    INTEGER, -- days active within the last 180-day window
            days_on_market_active INTEGER, -- days continuously active in current listing period across all channels
            days_on_site_active   INTEGER, -- days active on the dealer's own website
            seller_type          TEXT,
            inventory_type       TEXT,
            stock_num            TEXT,
            scraped_at_date      TEXT,
            in_transit           BOOLEAN,
            vehicle_status       TEXT,
            reference_price      REAL,
            price_change_percent REAL,
            reference_miles      INTEGER,
            dealer_id            INTEGER REFERENCES dealers(id),
            vehicle_build_id     INTEGER REFERENCES vehicle_builds(id)
        );

        CREATE TABLE IF NOT EXISTS vehicle_builds(
            id                   INT PRIMARY KEY,
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
            powertrain_type      TEXT
            UNIQUE(
                make,
                model,
                trim,
                year
            )
        );
    """)
    conn.commit()
    conn.close()

def upsert(obj: dataclass, db_path: str = "dreevo.db"):
    conn = connect(db_path)
    cursor = conn.cursor()
    table = obj.__table__
    _fields = fields(obj)
    columns = [f.name for f in _fields]
    values = [getattr(obj, f.name) for f in _fields]
    query = f"""
        INSERT INTO {table} ({columns})
        VALUES (?)
        ON CONFLICT(id)
        DO UP
    """
    cursor.executescript("""
            INSERT INTO table dealers (
                id          INTEGER PRIMARY KEY,
                marketcheck_id TEXT,
                name        TEXT,
                dealer_type TEXT,
                website     TEXT,
                street      TEXT,
                city        TEXT,
                state       TEXT,
                country     TEXT,
                zip         TEXT,
                phone       TEXT,
                contact_email TEXT
            );
           """)

