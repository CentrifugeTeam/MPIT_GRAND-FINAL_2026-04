from __future__ import annotations

from typing import List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import RoleDefinition


class RoleDefinitionCRUD:
    def list_roles(self, db: Session) -> List[RoleDefinition]:
        return db.query(RoleDefinition).order_by(RoleDefinition.key).all()

    def get_by_key(self, db: Session, key: str) -> Optional[RoleDefinition]:
        return db.query(RoleDefinition).filter(RoleDefinition.key == key).first()

    def key_exists(self, db: Session, key: str) -> bool:
        return self.get_by_key(db, key) is not None

    def create(
        self,
        db: Session,
        *,
        key: str,
        title: str,
        description: str | None = None,
        is_system: bool = False,
    ) -> RoleDefinition:
        row = RoleDefinition(
            key=key.strip().upper().replace(" ", "_"),
            title=title,
            description=description,
            is_system=is_system,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    def update(
        self,
        db: Session,
        key: str,
        *,
        title: str | None = None,
        description: str | None = None,
    ) -> Optional[RoleDefinition]:
        row = self.get_by_key(db, key)
        if not row:
            return None
        if row.is_system and title is not None:
            row.title = title
        if not row.is_system:
            if title is not None:
                row.title = title
            if description is not None:
                row.description = description
        elif description is not None:
            row.description = description
        db.commit()
        db.refresh(row)
        return row

    def delete(self, db: Session, key: str) -> bool:
        row = self.get_by_key(db, key)
        if not row or row.is_system:
            return False
        users_with = db.execute(
            text("SELECT COUNT(*) FROM users WHERE role = :k"),
            {"k": key},
        ).scalar()
        if users_with and int(users_with) > 0:
            raise ValueError("Role is assigned to users; reassign them first")
        db.delete(row)
        db.commit()
        return True


role_crud = RoleDefinitionCRUD()
