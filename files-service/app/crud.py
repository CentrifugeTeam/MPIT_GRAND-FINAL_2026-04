from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional
from app.models import File


def create_file(
    db: Session,
    file_id: UUID,
    file_name: str,
    file_path: str,
    file_size: int,
    mime_type: str,
    checksum: str,
    uploaded_by: Optional[UUID] = None,
) -> File:
    """Создать запись о файле в БД"""
    db_file = File(
        id=file_id,
        file_name=file_name,
        file_path=file_path,
        file_size=file_size,
        mime_type=mime_type,
        checksum=checksum,
        uploaded_by=uploaded_by,
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file


def get_file_by_id(db: Session, file_id: UUID) -> Optional[File]:
    """Получить файл по ID"""
    return db.query(File).filter(File.id == file_id).first()


def delete_file(db: Session, file_id: UUID) -> bool:
    """Удалить запись о файле из БД"""
    db_file = get_file_by_id(db, file_id)
    if db_file:
        db.delete(db_file)
        db.commit()
        return True
    return False
