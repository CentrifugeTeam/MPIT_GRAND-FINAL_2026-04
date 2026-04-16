from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, Form
from fastapi.responses import StreamingResponse
import io
from urllib.parse import quote
from app.schemas.files import FileUploadResponse, FileResponse
from app.services.files_service import FilesService
from app.api.auth import get_current_user

router = APIRouter()
files_service = FilesService()

@router.post("/upload", response_model=FileUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Загрузить файл в систему"""
    try:
        user_id = current_user.get("user_id")

        result = await files_service.upload_file(
            file=file,
            uploaded_by=user_id
        )

        return FileUploadResponse(**result)

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
    current_user: dict = Depends(get_current_user)
):
    """Скачать файл по ID"""
    try:
        metadata = await files_service.get_file_metadata(file_id)

        file_content = await files_service.download_file(file_id)

        filename = metadata.get("file_name") or "download"
        # Starlette/uvicorn require headers to be latin-1 encodable.
        # Use RFC 5987 for unicode filenames + a safe ASCII fallback.
        ascii_fallback = "".join(ch if 32 <= ord(ch) < 127 and ch not in {'"', "\\"} else "_" for ch in filename) or "download"
        content_disposition = f"attachment; filename=\"{ascii_fallback}\"; filename*=UTF-8''{quote(filename)}"

        return StreamingResponse(
            io.BytesIO(file_content),
            media_type=metadata.get("mime_type", "application/octet-stream"),
            headers={
                "Content-Disposition": content_disposition
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download file: {str(e)}"
        )

@router.get("/{file_id}", response_model=FileResponse)
async def get_file_metadata(
    file_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Получить метаданные файла"""
    try:
        result = await files_service.get_file_metadata(file_id)
        return FileResponse(**result)

    except HTTPException:
        raise

@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Удалить файл"""
    try:
        await files_service.delete_file(file_id)
        return None

    except HTTPException:
        raise

