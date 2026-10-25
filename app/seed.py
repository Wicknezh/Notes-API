from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.models import Role, User
from app.security import hash_password


DEMO_USERS = [
    ("admin", "admin12345", Role.ADMIN),
    ("alice", "alice12345", Role.USER),
    ("victor", "victor12345", Role.VIEWER),
]


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        for username, password, role in DEMO_USERS:
            if db.scalar(select(User).where(User.username == username)):
                print(f"skipped  {username} (already exists)")
                continue
            db.add(User(username=username, hashed_password=hash_password(password), role=role))
            print(f"created  {username} ({role.value})")
        db.commit()


if __name__ == "__main__":
    seed()