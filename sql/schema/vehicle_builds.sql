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
            engine_size          FLOAT,
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