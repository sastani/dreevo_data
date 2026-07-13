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