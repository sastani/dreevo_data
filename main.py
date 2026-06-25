from database import init_db
from catalog_pipeline.normalize import *
from catalog_pipeline.build_catalog import *
from market_pipeline.aggregate_market import compute_market_metrics
from market_pipeline.ingest_listings import ingest_listings

def main():
    init_db()
    normalize()
    build_catalog()
    ingest_listings()
    compute_market_metrics()


if __name__ == "__main__":
    main()
