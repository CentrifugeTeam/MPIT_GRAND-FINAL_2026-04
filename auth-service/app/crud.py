from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional, List
from uuid import UUID
from datetime import datetime
import hashlib
from app.models import User, RefreshToken
from app.schemas import UserCreate, UserUpdate
from app.role_crud import role_crud


class UserCRUD:
    def create_user(self, db: Session, user: UserCreate) -> User:
        """Создать пользователя"""
        if user.password != user.confirm_password:
            raise ValueError("Passwords do not match")

        role_key = (user.role or "USER").strip().upper().replace(" ", "_")
        if not role_crud.key_exists(db, role_key):
            raise ValueError(f"Unknown role: {role_key}")

        password_hash = hashlib.sha256(user.password.encode()).hexdigest()

        db_user = User(
            email=user.email,
            password_hash=password_hash,
            role=role_key,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """Получить пользователя по email"""
        return db.query(User).filter(User.email == email).first()

    def get_user_by_uuid(self, db: Session, user_uuid: UUID) -> Optional[User]:
        """Получить пользователя по UUID"""
        return db.query(User).filter(User.uuid == user_uuid).first()

    def get_all_users(self, db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """Получить всех пользователей"""
        return db.query(User).offset(skip).limit(limit).all()

    def update_user(self, db: Session, user_uuid: UUID, user_update: UserUpdate) -> Optional[User]:
        """Обновить пользователя"""
        db_user = self.get_user_by_uuid(db, user_uuid)
        if not db_user:
            return None

        update_data = user_update.model_dump(exclude_unset=True)
        if "role" in update_data and update_data["role"] is not None:
            rk = str(update_data["role"]).strip().upper().replace(" ", "_")
            if not role_crud.key_exists(db, rk):
                raise ValueError(f"Unknown role: {rk}")
            update_data["role"] = rk
        for field, value in update_data.items():
            setattr(db_user, field, value)

        db.commit()
        db.refresh(db_user)
        return db_user

    def update_user_by_email(self, db: Session, email: str, user_update: UserUpdate) -> Optional[User]:
        """Обновить пользователя по email"""
        db_user = self.get_user_by_email(db, email)
        if not db_user:
            return None

        update_data = user_update.model_dump(exclude_unset=True)
        if "role" in update_data and update_data["role"] is not None:
            rk = str(update_data["role"]).strip().upper().replace(" ", "_")
            if not role_crud.key_exists(db, rk):
                raise ValueError(f"Unknown role: {rk}")
            update_data["role"] = rk
        for field, value in update_data.items():
            setattr(db_user, field, value)

        db.commit()
        db.refresh(db_user)
        return db_user

    def verify_user(self, db: Session, user_uuid: UUID) -> Optional[User]:
        """Подтвердить email пользователя"""
        db_user = self.get_user_by_uuid(db, user_uuid)
        if not db_user:
            return None

        db_user.is_verified = True
        db.commit()
        db.refresh(db_user)
        return db_user

    def authenticate_user(self, db: Session, email: str, password: str) -> Optional[User]:
        """Аутентификация пользователя"""
        user = self.get_user_by_email(db, email)
        if not user:
            return None

        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if user.password_hash != password_hash:
            return None

        return user

    def update_user_role(self, db: Session, user_uuid: UUID, new_role: str) -> Optional[User]:
        """Обновить роль пользователя"""
        user = self.get_user_by_uuid(db, user_uuid)
        if not user:
            return None

        rk = str(new_role).strip().upper().replace(" ", "_")
        if not role_crud.key_exists(db, rk):
            raise ValueError(f"Unknown role: {rk}")

        user.role = rk
        db.commit()
        db.refresh(user)
        return user


class RefreshTokenCRUD:
    def create_refresh_token(self, db: Session, user_uuid: UUID, token: str, expires_at: datetime) -> RefreshToken:
        """Создать refresh токен"""
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        db_token = RefreshToken(
            user_uuid=user_uuid,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        db.add(db_token)
        db.commit()
        db.refresh(db_token)
        return db_token

    def get_refresh_token(self, db: Session, token: str) -> Optional[RefreshToken]:
        """Получить refresh токен"""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return (
            db.query(RefreshToken)
            .filter(
                and_(
                    RefreshToken.token_hash == token_hash,
                    RefreshToken.is_revoked == False,
                    RefreshToken.expires_at > datetime.utcnow(),
                )
            )
            .first()
        )

    def revoke_token(self, db: Session, token: str) -> bool:
        """Отозвать refresh токен"""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        db_token = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
        if not db_token:
            return False

        db_token.is_revoked = True
        db.commit()
        return True

    def revoke_all_user_tokens(self, db: Session, user_uuid: UUID) -> bool:
        """Отозвать все токены пользователя"""
        db.query(RefreshToken).filter(RefreshToken.user_uuid == user_uuid).update({"is_revoked": True})
        db.commit()
        return True


user_crud = UserCRUD()
refresh_token_crud = RefreshTokenCRUD()
