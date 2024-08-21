from typing import Optional
from sqlmodel import SQLModel, Field

from enum import Enum



####################################################
#   Auth models                                 ####
####################################################

class Token(SQLModel, table=False):
    access_token: str
    token_type: str

class UserData(SQLModel, table=False):
    username: str


####################################################
#   Scoring rules                               ####
####################################################

class ScoreRuleStatus(str, Enum):
    active = "active"
    skip = "skip"

class ScoreRule(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    service_re: Optional[str]
    object_type_re: Optional[str]
    object_re: Optional[str]
    field_re: Optional[str]
    field_type_re: Optional[str]
    risk_score: int
    status: ScoreRuleStatus = ScoreRuleStatus.active