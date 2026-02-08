from pydantic import BaseModel
from typing import List, Optional

class CaseCreate(BaseModel):
    description: Optional[str]
    symptoms: Optional[List[str]]
