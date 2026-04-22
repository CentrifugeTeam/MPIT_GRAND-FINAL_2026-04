from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    RoleDefinitionCreate,
    RoleDefinitionListResponse,
    RoleDefinitionResponse,
    RoleDefinitionUpdate,
)
from app.role_crud import role_crud
from app.api.users import require_admin

router = APIRouter()


@router.get("/", response_model=RoleDefinitionListResponse)
async def list_roles(
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    rows = role_crud.list_roles(db)
    return RoleDefinitionListResponse(
        roles=[RoleDefinitionResponse.model_validate(r, from_attributes=True) for r in rows]
    )


@router.post("/", response_model=RoleDefinitionResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    body: RoleDefinitionCreate,
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    if role_crud.key_exists(db, body.key):
        raise HTTPException(status_code=400, detail="Role key already exists")
    try:
        row = role_crud.create(
            db,
            key=body.key,
            title=body.title,
            description=body.description,
            is_system=False,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return RoleDefinitionResponse.model_validate(row, from_attributes=True)


@router.get("/{role_key}", response_model=RoleDefinitionResponse)
async def get_role(
    role_key: str,
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    row = role_crud.get_by_key(db, role_key.strip().upper())
    if not row:
        raise HTTPException(status_code=404, detail="Role not found")
    return RoleDefinitionResponse.model_validate(row, from_attributes=True)


@router.patch("/{role_key}", response_model=RoleDefinitionResponse)
async def patch_role(
    role_key: str,
    body: RoleDefinitionUpdate,
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    row = role_crud.update(
        db,
        role_key.strip().upper(),
        title=body.title,
        description=body.description,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Role not found")
    return RoleDefinitionResponse.model_validate(row, from_attributes=True)


@router.delete("/{role_key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_key: str,
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    try:
        ok = role_crud.delete(db, role_key.strip().upper())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if not ok:
        raise HTTPException(status_code=400, detail="Cannot delete system or unknown role")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
