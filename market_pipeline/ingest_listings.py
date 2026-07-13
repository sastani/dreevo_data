import json

from dotenv import load_dotenv
load_dotenv()

import re
from utils.file_utils import *
import time
from database import *
import requests
from models.listing import Listing
from models.dealer import Dealer
from models.marketplace import Marketplace
from models.vehicle_build import Vehicle_Build
from models.raw_marketcheck import Raw_Marketcheck
from datetime import datetime

API_KEY = os.environ.get("MARKETCHECK_API_KEY", "YOUR_MARKETCHECK_API_KEY")
API_ENDPOINTS = {
    "DEALER": "https://api.marketcheck.com/v2/search/car/active",
    "PRIVATE PARTY": "https://api.marketcheck.com/v2/search/car/fsbo/active",
    "AUCTION": "https://api.marketcheck.com/v2/search/car/auction/active"
}

REQUEST_DELAY_SEC = 0.25  # be polite about request rate
TIMEOUT_SEC = 15
MAX_RETRIES = 3
LISTING_ROWS = 50  # how many individual listing URLs to grab per make/model/year

YEAR_TOKEN_RE = re.compile(r"^(19|20)\d{2}$")

#all 48 contiguous states in U.S.
ABBREVIATION_TO_NAME = {
    "AL": "Alabama",
    "AR": "Arkansas",
    "AZ": "Arizona",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "FL": "Florida",
    "GA": "Georgia",
    "IA": "Iowa",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "MA": "Massachusetts",
    "MD": "Maryland",
    "ME": "Maine",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MO": "Missouri",
    "MS": "Mississippi",
    "MT": "Montana",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "NE": "Nebraska",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NV": "Nevada",
    "NY": "New York",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VA": "Virginia",
    "VT": "Vermont",
    "WA": "Washington",
    "WI": "Wisconsin",
    "WV": "West Virginia",
    "WY": "Wyoming",
    "DC": "District of Columbia",
}

REGION_TO_STATES = {
            "WEST": ["CA", "OR", "WA", "NV", "ID", "UT", "CO", "WY", "MT"],
            "MIDWEST": ["ND", "SD", "NE", "KS", "MN", "IA", "MO", "WI", "IL", "IN", "MI", "OH"],
            "SOUTHWEST": ["AZ", "NM", "TX", "OK"],
            "SOUTHEAST": ["AR", "LA", "MS", "TN", "AL", "KY", "GA", "WV", "VA", "NC", "SC", "FL", "MD", "DE"],
            "NORTHEAST": ["CT", "DC", "HI", "ME", "MA", "NH", "NJ", "NY", "PA", "RI", "VT"]
}

STATE_TO_REGION = {
    "CA": "WEST", "OR": "WEST", "WA": "WEST", "NV": "WEST", "ID": "WEST",
    "UT": "WEST", "CO": "WEST", "WY": "WEST", "MT": "WEST",
    "ND": "MIDWEST", "SD": "MIDWEST", "NE": "MIDWEST", "KS": "MIDWEST",
    "MN": "MIDWEST", "IA": "MIDWEST", "MO": "MIDWEST", "WI": "MIDWEST",
    "IL": "MIDWEST", "IN": "MIDWEST", "MI": "MIDWEST", "OH": "MIDWEST",
    "AZ": "SOUTHWEST", "NM": "SOUTHWEST", "TX": "SOUTHWEST", "OK": "SOUTHWEST",
    "AR": "SOUTHEAST", "LA": "SOUTHEAST", "MS": "SOUTHEAST", "TN": "SOUTHEAST",
    "AL": "SOUTHEAST", "KY": "SOUTHEAST", "GA": "SOUTHEAST", "WV": "SOUTHEAST",
    "VA": "SOUTHEAST", "NC": "SOUTHEAST", "SC": "SOUTHEAST", "FL": "SOUTHEAST",
    "MD": "SOUTHEAST", "DE": "SOUTHEAST",
    "CT": "NORTHEAST", "DC": "NORTHEAST", "HI": "NORTHEAST", "ME": "NORTHEAST",
    "MA": "NORTHEAST", "NH": "NORTHEAST", "NJ": "NORTHEAST", "NY": "NORTHEAST",
    "PA": "NORTHEAST", "RI": "NORTHEAST", "VT": "NORTHEAST"
}

def transform_input():
    uber_model_df = read_file("Uber_Model_Production_Years.xlsx")
    uber_model_df['first_possible_year'] = uber_model_df[['minimum_year', 'first_year_produced']].max(axis=1)
    uber_model_df['last_possible_year'] = uber_model_df['last_year_produced']
    # transform model columns for bmws and mercedes to match MarketCheck API model field
    # find all bmw 3,5, etc series models by using 'model_family' column and use it instead of 'model' column as 'model'
    bmw_model_mask = (uber_model_df['make'] == 'BMW') & (uber_model_df['model_family'].notna())
    uber_model_df.loc[bmw_model_mask, 'model'] = uber_model_df['model_family'].str.replace("-", " ")
    # find all mercedes models and use 'model_family' column instead of 'model' column
    mercedes_model_mask = (uber_model_df['make'] == 'Mercedes-Benz')
    uber_model_df.loc[mercedes_model_mask, 'model'] = uber_model_df['model_family']
    # dedup dataframe since there are duplicate entries for both 'black' and 'comfort' as well as bmw/mercedes models
    uber_model_df = uber_model_df.groupby(['make', 'model'], as_index=False).agg(
        min_year=('first_possible_year', 'min'),
        max_year=('last_possible_year', 'max')
    )
    return uber_model_df

def fetch_listings():
    def get_data(base_url, params):
        for attempt in range(MAX_RETRIES):
            try:
                resp = requests.get(base_url, params=params, timeout=TIMEOUT_SEC)
                if resp.status_code == 429:
                    time.sleep(2 ** attempt)
                    continue
                resp.raise_for_status()
                return resp.json()
            except requests.RequestException as e:
                print(f"Request failed (attempt {attempt + 1}): {e}")
        return None

    def log_and_process(listing_dict, listing_type, endpoint, req_params):
        marketcheck_id = listing_dict.get("id")
        fetched_at = datetime.now().strftime("%m-%d-%Y %H:%M:%S")
        listing_json = json.dumps(listing_dict)
        params_json = json.dumps(req_params)
        insert([Raw_Marketcheck(marketcheck_id, fetched_at, endpoint, listing_type, params_json, listing_json)])

    def process_page(listing_dicts, listing_type, api_endpoint, req_params):
        dealer_objs = list()
        marketplace_objs = list()
        build_objs = list()
        listing_objs = list()
        for listing_dict in listing_dicts:
            log_and_process(listing_dict, listing_type, api_endpoint, req_params)
            listing_dict["listing_type"] = listing_type
            build_dict = listing_dict.get("build", {})
            listing_dict.update(build_dict)
            dealer_dict = listing_dict.get("dealer")
            if listing_type == "DEALER":
                listing_dict["seller_name"] = dealer_dict.get("name")
                listing_dict["city"] = dealer_dict.get("city")
                listing_dict["state"] = dealer_dict.get("state")
                listing_dict["zip"] = dealer_dict.get("zip")
                dealer = Dealer.from_dict(dealer_dict)
                dealer_objs.append(dealer)
            elif listing_type == "PRIVATE PARTY":
                if "car_location" in listing_dict:
                    car_location_dict = listing_dict.get("car_location")
                    listing_dict["seller_name"] = car_location_dict.get("seller_name")
                    listing_dict["city"] = car_location_dict.get("city")
                    listing_dict["state"] = car_location_dict.get("state")
                    listing_dict["zip"] = car_location_dict.get("zip")
                else:
                    listing_dict["seller_name"] = dealer_dict.get("name")
                    listing_dict["city"] = dealer_dict.get("city")
                    listing_dict["state"] = dealer_dict.get("state")
                    listing_dict["zip"] = dealer_dict.get("zip")
                if dealer_dict.get("name") == "Private Seller":
                    listing_dict["seller_name"] = None
                marketplace = Marketplace.from_dict(dealer_dict)
                marketplace_objs.append(marketplace)
            else:
                if "car_location" in listing_dict:
                    car_location_dict = listing_dict.get("car_location")
                    listing_dict["seller_name"] = car_location_dict.get("seller_name")
                    listing_dict["city"] = car_location_dict.get("city")
                    listing_dict["state"] = car_location_dict.get("state")
                    listing_dict["zip"] = car_location_dict.get("zip")
                marketplace = Marketplace.from_dict(dealer_dict)
                marketplace_objs.append(marketplace)
            state = listing_dict.get("state")
            if state:
                listing_dict["region"] = STATE_TO_REGION.get(state)
            listing = Listing.from_dict(listing_dict)
            listing_objs.append(listing)
            vehicle_build = Vehicle_Build.from_dict(build_dict)
            build_objs.append(vehicle_build)
        dealer_ids = upsert(dealer_objs)
        build_ids = upsert(build_objs)
        marketplace_ids = upsert(marketplace_objs)
        for i, listing_obj in enumerate(listing_objs):
            listing_obj.dealer_id = dealer_ids[i] if i < len(dealer_ids) else None
            listing_obj.vehicle_build_id = build_ids[i] if i < len(build_ids) else None
            listing_obj.marketplace_id = marketplace_ids[i] if i < len(marketplace_ids) else None
        insert(listing_objs)

    init_db()
    uber_model_df = transform_input()
    for row in uber_model_df.itertuples(index=True):
        for y in range(row.min_year, row.max_year+1):
                for listing_type, api_endpoint_url in API_ENDPOINTS.items():
                    base_params = {
                        "api_key": API_KEY,
                        "car_type": "used",
                        "make": row.make,
                        "model": row.model,
                        "year": str(y),
                        "rows": LISTING_ROWS,
                        "country": "us",
                    }
                    if listing_type == "DEALER":
                        requests_list = []
                        states_list = list(ABBREVIATION_TO_NAME.keys())
                        for i in range(0, len(states_list), 3):
                            requests_list.append({**base_params, "state": ",".join(states_list[i:i+3])})
                    elif listing_type == "PRIVATE PARTY":
                        requests_list = []
                        states_list = list(ABBREVIATION_TO_NAME.keys())
                        half = len(states_list) // 2
                        half_of_states = [states_list[:half], states_list[half:]]
                        for chunk in half_of_states:
                            requests_list.append({**base_params, "state": ",".join(chunk)})
                    else:
                        requests_list = [base_params]
                    for params in requests_list:
                        data = get_data(api_endpoint_url, params)
                        if data is None:
                            continue
                        count = data.get("num_found", 0)
                        if count > 1500:
                            with open(os.path.join(DATA_DIR_PATH, "large_responses.txt"), "a") as f:
                                f.write(f"count: {count}\nparams: {json.dumps(params)}\n---\n")
                        process_page(data.get("listings", []), listing_type, api_endpoint_url, params)
                        offset = LISTING_ROWS
                        while offset < count:
                            time.sleep(REQUEST_DELAY_SEC)
                            paged_params = {**params, "start": offset}
                            paged_data = get_data(api_endpoint_url, paged_params)
                            if paged_data is None:
                                break
                            process_page(paged_data.get("listings", []), listing_type, api_endpoint_url, paged_params)
                            offset += LISTING_ROWS

fetch_listings()