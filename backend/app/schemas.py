from pydantic import BaseModel
from typing import Dict, Union

class NDVIRequest(BaseModel):
    aoi: Dict  # Accepts Feature or FeatureCollection
    past_year: int
    present_year: int
