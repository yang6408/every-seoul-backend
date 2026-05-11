from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

database_url = settings.sqlalchemy_database_url

connect_args = {}
if database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    database_url,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app.db.models import bookmark, newsletter, push_subscription, session, user  # noqa: F401

    Base.metadata.create_all(bind=engine)


def ensure_user_profile_columns() -> None:
    inspector = inspect(engine)
    if not inspector.has_table("users"):
        return

    existing_columns = {column["name"] for column in inspector.get_columns("users")}
    columns = {
        "age": "INTEGER",
        "has_children": "BOOLEAN DEFAULT FALSE",
        "children_count": "INTEGER",
        "employment_status": "VARCHAR(50) DEFAULT ''",
    }

    with engine.begin() as connection:
        for name, definition in columns.items():
            if name not in existing_columns:
                connection.execute(text(f"ALTER TABLE users ADD COLUMN {name} {definition}"))
