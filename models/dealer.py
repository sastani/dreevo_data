from dataclasses import dataclass
from typing import Optional


@dataclass
class Dealer:
    __table__="dealers"
    marketcheck_id = str
    name: str
    dealer_type: Optional[str]
    website: Optional[str]
    street: Optional[str]
    city: Optional[str]
    state: Optional[str]
    country: Optional[str]
    zip: Optional[str]
    phone: Optional[str]
    contact_email: Optional[str]