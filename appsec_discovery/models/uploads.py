from pydantic import BaseModel

class DefectdojoImportScanRequest(BaseModel):
    key: str
    name: str
    type: str
    file: int
    line: int
    properties: str
    fields: str
    score: str

class DefectdojoProjectTypeRequest(BaseModel):
    key: str
    name: str

class DiscoveryImportScanRequest(BaseModel):
    key: str
    name: str
    type: str