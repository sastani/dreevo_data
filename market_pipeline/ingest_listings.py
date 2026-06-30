from dotenv import load_dotenv
load_dotenv()

import os
import re
import pandas as pd
from utils.file_utils import *
import sys
import time
from typing import List, Optional, Tuple

import openpyxl
import requests

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

def fetch_listings():
    def get_data(base_url, params):
        for attempt in range(MAX_RETRIES):
            resp = requests.get(base_url, params=params, timeout=TIMEOUT_SEC)
            if resp.status_code == 429:
                time.sleep(2 ** attempt)
                continue
            resp.raise_for_status()
            return resp.json()
        return None

    uber_model_df = read_file("Uber_Model_Production_Years.xlsx")
    uber_model_df['first_possible_year'] = uber_model_df[['minimum year', 'first_year_produced']].max(axis=1)
    uber_model_df['last_possible_year'] = uber_model_df['last_year_produced']
    #transform model columns for bmws and mercedes to match MarketCheck API model field
    #find all bmw 3,5, etc series models by using 'model_family' column and use it instead of 'model' column as 'model'
    bmw_model_mask = (uber_model_df['make'] == 'BMW') & (uber_model_df['model_family'].notna())
    uber_model_df.loc[bmw_model_mask, 'model'] = uber_model_df['model_family'].str.replace("-", " ")
    # find all mercedes models and use 'model_family' column instead of 'model' column
    mercedes_model_mask = (uber_model_df['make'] == 'Mercedes-Benz')
    uber_model_df.loc[mercedes_model_mask, 'model'] = uber_model_df['model_family']
    #dedup dataframe since there are duplicate entries for both 'black' and 'comfort' as well as bmw/mercedes models
    uber_model_df = uber_model_df.groupby(['make', 'model'], as_index=False).agg(
        min_year=('first_possible_year', 'min'),
        max_year=('last_possible_year', 'max')
    )
    for row in uber_model_df.itertuples(index=True):
        for y in range(row.min_year, row.max_year+1):
                for listing_type, api_endpoint_url in API_ENDPOINTS:
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
                        for region, state_list in REGION_TO_STATES:
                            state_string = ",".join(state_list)
                            base_params["state"] = state_string
                    data = get_data(api_endpoint_url, base_params)
                    count = data.get("num_found", 0)



fetch_listings()