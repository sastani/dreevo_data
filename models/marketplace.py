from dataclasses import dataclass, field, fields
from typing import Optional

@dataclass
class Marketplace:
    __table__="marketplaces"
    marketcheck_id: str = field(metadata={"json_key": "id"})
    name: str
    website: str

    @classmethod
    def from_dict(cls, data: dict):
        kwargs = {}
        for f in fields(cls):
            # Read the alias from metadata, fallback to the attribute name
            json_key = f.metadata.get("json_key", f.name)
            kwargs[f.name] = data.get(json_key)
        return cls(**kwargs)