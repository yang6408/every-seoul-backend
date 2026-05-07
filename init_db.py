"""
DB 초기화 스크립트
실행: python init_db.py
"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from app.core.config import settings
from app.db.session import Base, engine

# 1. everyseoul 데이터베이스 생성 (없으면)
def create_database():
    url = settings.DATABASE_URL
    # postgres 기본 DB로 먼저 접속
    import re
    match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', url)
    user, password, host, port, dbname = match.groups()

    conn = psycopg2.connect(host=host, port=int(port), user=user, password=password, dbname='postgres')
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{dbname}'")
    if not cur.fetchone():
        cur.execute(f'CREATE DATABASE "{dbname}"')
        print(f"데이터베이스 '{dbname}' 생성 완료")
    else:
        print(f"데이터베이스 '{dbname}' 이미 존재")

    cur.close()
    conn.close()

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
