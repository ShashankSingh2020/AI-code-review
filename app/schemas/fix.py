from pydantic import BaseModel
from typing import Optional

class FixRequest(BaseModel):
    rule_id: str
    message: str
    file_path: str
    line: int
    code_context: Optional[str] = ""

class FixResponse(BaseModel):
    explanation: str
    suggested_patch: str