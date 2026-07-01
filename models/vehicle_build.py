from dataclasses import dataclass, field, fields
from typing import Optional

@dataclass
class Vehicle_Build:
    __table__="vehicle_builds"
    year: int
    make: str
    model: str
    trim: str
    version: str
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

    @classmethod
    def from_dict(cls, data: dict):
        kwargs = {}
        for f in fields(cls):
            # Read the alias from metadata, fallback to the attribute name
            json_key = f.metadata.get("json_key", f.name)
            kwargs[f.name] = data.get(json_key)
        return cls(**kwargs)