from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class SignupRequest(BaseModel):
    company_name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class KnowledgeDocumentOut(BaseModel):
    id: str
    filename: str
    uploaded_at: datetime

    class Config:
        from_attributes = True

class DocumentChunkOut(BaseModel):
    id: str
    chunk_index: int
    chunk_text: str

    class Config:
        from_attributes = True