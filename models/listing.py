from dataclasses import dataclass
from typing import Optional

@dataclass
class Listing:
    __table__="listings"
    marketcheck_id: str
    year: Optional[int]
    make: Optional[str]
    model: Optional[str]
    trim: Optional[str]
    version: Optional[str]
    vin: str
    heading: Optional[str]
    price: Optional[float]
    mileage: Optional[int]
    msrp: Optional[float]
    listing_url: Optional[str]
    carfax_1_owner: Optional[bool]
    carfax_clean_title: Optional[bool]
    exterior_color: Optional[str]
    interior_color: Optional[str]
    base_ext_color: Optional[str]
    base_int_color: Optional[str]
    days_on_market: Optional[int]
    days_on_market_180: Optional[int]
    days_on_market_active: Optional[int]
    days_on_site_active: Optional[int]
    seller_type: Optional[str]
    inventory_type: Optional[str]
    stock_num: Optional[str]
    scraped_at_date: Optional[str]
    in_transit: Optional[bool]
    vehicle_status: Optional[str]
    reference_price: Optional[float]
    price_change_percent: Optional[float]
    reference_miles: Optional[int]
    dealer_id: Optional[int]
    vehicle_build_id: Optional[int]