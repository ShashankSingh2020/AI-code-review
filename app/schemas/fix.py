
from pydantic import BaseModel


class FixRequest(BaseModel):
    rule_id: str
    message: str
    file_path: str
    line: int
    code_context: str | None = ""

class FixResponse(BaseModel):
    explanation: str
    suggested_patch: str
