from pydantic import BaseModel
from typing import List

class Evidence(BaseModel):
    pmid: str
    excerpt: str

class MedicalAnswer(BaseModel):
    question: str
    answer_summary: str
    evidence: List[Evidence]
    confidence: float
