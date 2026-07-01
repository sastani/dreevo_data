from dataclasses import dataclass, field, fields
from typing import Optional

@dataclass
class Listing:
    __table__="listings"
    marketcheck_id: str = field(metadata={"json_key": "id"})
    year: int
    make: str
    model: str
    trim: str
    version: str
    vin: str
    heading: Optional[str]
    seller_name: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip: Optional[str]
    region: Optional[str]
    listing_type: str
    price: Optional[float]
    buy_now_price: Optional[float]
    mileage: Optional[int] = field(metadata={"json_key": "miles"})
    msrp: Optional[float]
    listing_url: Optional[str] = field(metadata={"json_key": "vdp_url"})
    carfax_1_owner: Optional[bool]
    carfax_clean_title: Optional[bool]
    exterior_color: Optional[str]
    interior_color: Optional[str]
    base_exterior_color: Optional[str] = field(metadata={"json_key": "base_ext_color"})
    base_interior_color: Optional[str] = field(metadata={"json_key": "base_int_color"})
    days_on_market: Optional[int] = field(metadata={"json_key": "dom"})
    days_on_market_180: Optional[int] = field(metadata={"json_key": "dom_180"})
    days_on_market_active: Optional[int] = field(metadata={"json_key": "dom_active"})
    days_on_site_active: Optional[int]  = field(metadata={"json_key": "dos_active"})
    inventory_type: Optional[str]
    stock_num: Optional[str] = field(metadata={"json_key": "stock_no"})
    scraped_at_date: Optional[str]
    in_transit: Optional[bool]
    vehicle_status: Optional[str]
    reference_price: Optional[float] = field(metadata={"json_key": "ref_price"})
    reference_price_date: Optional[int] = field(metadata={"json_key": "ref_price_dt"})
    price_change_percent: Optional[float]
    reference_miles: Optional[int] = field(metadata={"json_key": "ref_miles"})
    reference_miles_date: Optional[int] = field(metadata={"json_key": "ref_miles_dt"})
    source: Optional[str]
    dealer_id: Optional[int] = None
    marketplace_id: Optional[int] = None
    vehicle_build_id: Optional[int] = None

    @classmethod
    def from_dict(cls, data: dict):
        kwargs = {}
        for f in fields(cls):
            # Read the alias from metadata, fallback to the attribute name
            json_key = f.metadata.get("json_key", f.name)
            kwargs[f.name] = data.get(json_key)
        return cls(**kwargs)