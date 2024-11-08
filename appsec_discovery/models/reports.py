from pydantic import BaseModel
from typing import List, Dict


class SarifReport(BaseModel):
    file: str
    object_type: str
    object_name: str

class JsonReport(BaseModel):
    file: str
    object_type: str
    object_name: str

class DiffReport(BaseModel):
    file: str
    object_type: str
    object_name: str

