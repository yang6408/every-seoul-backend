"""
DB 초기화 스크립트
실행: python init_db.py
"""
from app.db.bootstrap import create_database_if_missing
from app.db.session import Base, engine


# 1. everyseoul 데이터베이스 생성 (없으면)
def create_database():
    create_database_if_missing()
    print("데이터베이스 확인 완료")


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
