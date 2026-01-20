from pydantic import BaseModel
from typing import List

class NDVIRequest(BaseModel):
    aoi: List
    past_start: str
    past_end: str
    present_start: str
    present_end: str
    threshold: float
