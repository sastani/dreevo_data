from dataclasses import dataclass, field, fields
from typing import Optional

@dataclass
class Raw_Marketcheck:
    __table__="raw_marketcheck"
    marketcheck_id: str
    fetched_at:  str
    api_endpoint: str
    listing_type: str
    query_params: str
    listing_json: str

