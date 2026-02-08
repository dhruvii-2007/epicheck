from pydantic import BaseModel

class ReviewCreate(BaseModel):
    case_id: str
    notes: str
    decision: str
