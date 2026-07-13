CREATE TABLE IF NOT EXISTS raw_marketcheck(
            id             INTEGER PRIMARY KEY,
            marketcheck_id TEXT,
            fetched_at     TEXT,
            api_endpoint   TEXT,
            listing_type   TEXT,
            query_params   TEXT,
            listing_json   TEXT NOT NULL
        );