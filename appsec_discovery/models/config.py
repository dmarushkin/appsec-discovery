from pydantic import BaseModel
from typing import List, Dict, Optional

class ExcludeScan(BaseModel):
    file: Optional[str]
    parser: Optional[str]
    object_name: Optional[str]
    object_type: Optional[str]

class ExcludeScoring(BaseModel):
    file: Optional[str]
    parser: Optional[str]
    object_name: Optional[str]
    object_type: Optional[str]
    prop_name: Optional[str]
    field_name: Optional[str]
    field_type: Optional[str]
    tag: Optional[str]
    keyword: Optional[str]

class AiParams(BaseModel):
    model_id: str
    model_folder: str
    gguf_file: str
    prompt: str

class ScoreConfig(BaseModel):
    parsers: List[str] = ['all']
    object_types: List[str] = ['all']
    score_tags: Dict[str,Dict[str,List[str]]] = {}
    ai_params: Optional[AiParams]
    exclude_scan: List[ExcludeScan] = []
    exclude_scoring: List[ExcludeScoring] = []

