from dataclasses import dataclass
from typing import Optional

@dataclass
class Vehicle_Build:
    __table__="vehicle_builds"
    year: int
    make: str
    model: str
    trim: str
    body_type: Optional[str]
    transmission: Optional[str]
    drivetrain: Optional[str]
    fuel_type: Optional[str]
    engine: Optional[str]
    engine_size: Optional[float]
    engine_block: Optional[str]
    doors: Optional[int]
    cylinders: Optional[int]
    made_in: Optional[str]
    highway_mpg: Optional[int]
    city_mpg: Optional[int]
    powertrain_type: Optional[str]