from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class FileUploadResponse(BaseModel):
    id: str
    file_name: str
    file_path: str
    file_size: int
    mime_type: str
    checksum: str
    uploaded_by: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class FileResponse(BaseModel):
    id: str
    file_name: str
    file_size: int
    mime_type: str
    checksum: str
    uploaded_by: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

