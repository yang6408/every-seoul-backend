# every-seoul-backend

FastAPI 기반 에브리 서울 백엔드입니다.

## 로컬 실행

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

API 문서: <http://localhost:8000/docs>

헬스체크:

```bash
curl http://localhost:8000/health
```

## Docker Compose 실행

```bash
copy .env.example .env
docker compose up --build
```

기본 Compose 구성은 API와 PostgreSQL을 함께 실행합니다. 앱은 `http://localhost:8000`에서 열립니다.

## 환경 변수

| 이름 | 설명 | 기본값 |
| --- | --- | --- |
| `APP_NAME` | FastAPI 앱 이름 | `에브리 서울 API` |
| `APP_VERSION` | 앱 버전 | `1.0.0` |
| `ENVIRONMENT` | 실행 환경 표시값 | `local` |
| `DEBUG` | FastAPI debug 모드 | `false` |
| `DB_HOST` | PostgreSQL 호스트 | `localhost` |
| `DB_PORT` | PostgreSQL 포트 | `5432` |
| `DB_USER` | PostgreSQL 사용자 | `dev` |
| `DB_PASSWORD` | PostgreSQL 비밀번호 | `1234` |
| `DB_NAME` | PostgreSQL 데이터베이스 이름 | `DevDB` |
| `SEOUL_OPEN_API_KEY` | 서울 열린데이터광장 API 키 | 없음 |
| `OPENROUTER_API_KEY` | 뉴스레터 브리핑 생성용 OpenRouter API 키 | 없음 |
| `GOOGLE_CLIENT_ID` | Google Identity Services ID token 검증용 OAuth Client ID | 없음 |
| `ADMIN_API_KEY` | 관리자 API 수동 실행 토큰 | 없음 |
| `CREATE_DATABASE` | 시작 시 PostgreSQL 데이터베이스가 없으면 생성 | `false` |
| `CREATE_DB_TABLES` | 시작 시 SQLAlchemy 테이블 생성 | `false` |
| `ENABLE_SCHEDULER` | 매일 04:00 KST 뉴스레터 파이프라인 자동 실행 | `true` |
| `CORS_ORIGINS` | 쉼표로 구분한 허용 Origin 목록 | 없음 |
| `UVICORN_WORKERS` | 컨테이너 실행 시 Uvicorn worker 수 | `1` |

운영에서는 보통 `CREATE_DATABASE=false`, `CREATE_DB_TABLES=false`를 유지하고 Alembic 같은 마이그레이션 도구를 붙이는 것을 권장합니다. 초기 개발/스테이징이나 Docker Compose에서는 `true`로 켜면 됩니다.

## 뉴스레터 수집 파이프라인

뉴스레터는 백엔드 파이프라인이 서울 RSS, 문화행사, 생활 센서 데이터를 수집한 뒤 자치구별 브리핑을 생성해 DB에 저장하면 만들어집니다. `ENABLE_SCHEDULER=true`일 때 매일 `04:00 KST`에 자동 실행됩니다.

배포 직후 또는 테스트 중 즉시 실행하려면 관리자 API를 호출합니다.

```bash
curl -X POST http://localhost:8000/api/admin/pipeline/trigger \
  -H "X-Admin-Token: $ADMIN_API_KEY"
```

프로덕션에서는 `ADMIN_API_KEY`가 설정되어 있어야 하며, 요청 헤더의 `X-Admin-Token` 값이 일치해야 합니다. 로컬 개발 환경에서 `ADMIN_API_KEY`를 비워두면 토큰 없이 호출할 수 있습니다.

실행 후 오늘 생성된 뉴스레터는 다음 API로 확인할 수 있습니다.

```bash
curl "http://localhost:8000/api/newsletters/today?district=강남구"
```

파이프라인은 자치구별 RSS 데이터와 문화행사 데이터가 없으면 해당 자치구 생성을 건너뜁니다. OpenRouter 또는 서울 열린데이터광장 키가 잘못되어도 생성 결과가 비어 있을 수 있으므로 API 로그를 함께 확인하세요.

## 테스트

```bash
python -m pytest
```

서울 열린데이터광장 통합 테스트는 외부 API와 키가 필요하므로 기본적으로 스킵됩니다.

```bash
RUN_INTEGRATION_TESTS=1 python -m pytest
```
