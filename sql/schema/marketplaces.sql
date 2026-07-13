 CREATE TABLE IF NOT EXISTS marketplaces(
            id          INTEGER PRIMARY KEY,
            marketcheck_id INT UNIQUE,
            name          TEXT,
            website       TEXT UNIQUE NOT NULL
        );