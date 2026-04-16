from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from uuid import UUID, uuid4
from typing import Optional
from app.database import get_db
from app.schemas import FileUploadResponse, FileResponse as FileResponseSchema
from app.services.storage import StorageService
import app.crud as crud

router = APIRouter()
storage_service = StorageService()

@router.post("/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    uploaded_by: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Загрузить файл в систему"""
    try:
        file_id = uuid4()

        file_path, file_size, checksum = await storage_service.save_file(
            file=file,
            file_id=file_id
        )

        mime_type = file.content_type or "application/octet-stream"

        uploaded_by_uuid = UUID(uploaded_by) if uploaded_by else None

        db_file = crud.create_file(
            db=db,
            file_id=file_id,
            file_name=file.filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            checksum=checksum,
            uploaded_by=uploaded_by_uuid
        )

        return FileUploadResponse(
            id=str(db_file.id),
            file_name=db_file.file_name,
            file_path=db_file.file_path,
            file_size=db_file.file_size,
            mime_type=db_file.mime_type,
            checksum=db_file.checksum,
            uploaded_by=str(db_file.uploaded_by) if db_file.uploaded_by else None,
            created_at=db_file.created_at
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid UUID format: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )

@router.get("/{file_id}/download")
async def download_file(
    file_id: str,
    db: Session = Depends(get_db)
):
    """Скачать файл по ID"""
    try:
        file_uuid = UUID(file_id)

        db_file = crud.get_file_by_id(db, file_uuid)
        if not db_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )

        file_path = storage_service.get_file_path(db_file.file_path)

        return FileResponse(
            path=str(file_path),
            filename=db_file.file_name,
            media_type=db_file.mime_type
        )

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file_id format"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download file: {str(e)}"
        )

@router.get("/{file_id}", response_model=FileResponseSchema)
async def get_file_metadata(
    file_id: str,
    db: Session = Depends(get_db)
):
    """Получить метаданные файла"""
    try:
        file_uuid = UUID(file_id)

        db_file = crud.get_file_by_id(db, file_uuid)
        if not db_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )

        return FileResponseSchema(
            id=str(db_file.id),
            file_name=db_file.file_name,
            file_size=db_file.file_size,
            mime_type=db_file.mime_type,
            checksum=db_file.checksum,
            uploaded_by=str(db_file.uploaded_by) if db_file.uploaded_by else None,
            created_at=db_file.created_at,
            updated_at=db_file.updated_at
        )

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file_id format"
        )

@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: str,
    db: Session = Depends(get_db)
):
    """Удалить файл"""
    try:
        file_uuid = UUID(file_id)

        db_file = crud.get_file_by_id(db, file_uuid)
        if not db_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )

        storage_service.delete_file(db_file.file_path)

        crud.delete_file(db, file_uuid)

        return None

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file_id format"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}"
        )
