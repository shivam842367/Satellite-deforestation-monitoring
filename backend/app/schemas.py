from pydantic import BaseModel
from typing import List

class Geometry(BaseModel):
    type: str
    coordinates: List[List[List[float]]]

class AnalyzeRequest(BaseModel):
    geometry: Geometry
    past_year: int
    present_year: int
