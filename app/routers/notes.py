from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select

from app.deps import CurrentUser, DbSession, require_roles
from app.models import Note, Role, User
from app.schemas import NoteCreate, NoteOut, NoteUpdate

router = APIRouter(prefix="/notes", tags=["notes"])


Writer = Annotated[User, Depends(require_roles(Role.ADMIN, Role.USER))]


def get_note_or_404(db: DbSession, note_id: int) -> Note:
    note = db.get(Note, note_id)
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    return note


def ensure_can_modify(user: User, note: Note) -> None:
    """Admins can modify any note; Users only their own."""
    if user.role != Role.ADMIN and note.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only modify your own notes",
        )


@router.get("", response_model=list[NoteOut])
def list_notes(
    db: DbSession,
    _: CurrentUser, 
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    stmt = select(Note).order_by(Note.id).offset(skip).limit(limit)
    return db.scalars(stmt).all()


@router.get("/{note_id}", response_model=NoteOut)
def get_note(note_id: int, db: DbSession, _: CurrentUser):
    return get_note_or_404(db, note_id)


@router.post("", response_model=NoteOut, status_code=status.HTTP_201_CREATED)
def create_note(data: NoteCreate, db: DbSession, user: Writer):
    note = Note(title=data.title, content=data.content, owner_id=user.id)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.put("/{note_id}", response_model=NoteOut)
def update_note(note_id: int, data: NoteUpdate, db: DbSession, user: Writer):
    note = get_note_or_404(db, note_id)
    ensure_can_modify(user, note)

    for field, value in data.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(note, field, value)

    db.commit()
    db.refresh(note)
    return note


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(note_id: int, db: DbSession, user: Writer):
    note = get_note_or_404(db, note_id)
    ensure_can_modify(user, note)
    db.delete(note)
    db.commit()