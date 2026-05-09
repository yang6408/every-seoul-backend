"""
DB 초기화 스크립트
실행: python init_db.py
"""
import psycopg
from sqlalchemy.engine import make_url

from app.core.config import settings
from app.db.session import Base, engine


# 1. everyseoul 데이터베이스 생성 (없으면)
def create_database():
    url = make_url(settings.sqlalchemy_database_url)
    dbname = url.database
    if not dbname:
        raise RuntimeError("DATABASE_URL에 데이터베이스 이름이 없습니다.")

    with psycopg.connect(
        host=url.host,
        port=url.port or 5432,
        user=url.username,
        password=url.password,
        dbname="postgres",
        autocommit=True,
    ) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
            if not cur.fetchone():
                cur.execute(f'CREATE DATABASE "{dbname}"')
                print(f"데이터베이스 '{dbname}' 생성 완료")
            else:
                print(f"데이터베이스 '{dbname}' 이미 존재")


# 2. 모든 테이블 생성
def create_tables():
    import app.db.models.user       # noqa
    import app.db.models.newsletter  # noqa
    Base.metadata.create_all(bind=engine)
    print("테이블 생성 완료: users, newsletters, user_newsletter_matches")


if __name__ == "__main__":
    print("=== DB 초기화 시작 ===")
    create_database()
    create_tables()
    print("=== 완료 ===")
