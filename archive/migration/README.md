# Garden6 MongoDB to Supabase Migration

Garden6 프로젝트의 MongoDB slack_messages 컬렉션을 Supabase PostgreSQL로 마이그레이션하는 도구입니다.

## 개요

이 마이그레이션 도구는 다음 작업을 수행합니다:
- MongoDB 덤프 파일(BSON)에서 데이터를 읽기
- Supabase PostgreSQL에 garden6 스키마 생성
- slack_messages 테이블 및 관련 인덱스, 뷰 생성
- 데이터를 배치 단위로 효율적으로 마이그레이션

## 사전 준비사항

1. **Python 3.6 이상**
2. **MongoDB 덤프 파일** (slack_messages.bson)
3. **Supabase 프로젝트** 및 연결 정보
   - Host, Port, Database, User, Password

## 설치

1. 필요한 Python 패키지 설치:
```bash
pip install -r requirements.txt
```

## 설정

1. 설정 파일 준비:
```bash
cp migration_config.yaml.sample migration_config.yaml
```

2. `migration_config.yaml` 파일을 편집하여 실제 설정값 입력:
```yaml
# Supabase PostgreSQL 연결 정보
supabase:
  host: aws-0-ap-northeast-2.pooler.supabase.com
  port: 6543
  database: postgres
  user: postgres.your_project_id
  password: your_actual_password  # 실제 비밀번호로 교체
  schema: garden6

# MongoDB 덤프 파일 정보
mongodb:
  bson_file_path: /path/to/slack_messages.bson  # 실제 경로로 교체

# 마이그레이션 설정
migration:
  batch_size: 1000
  log_level: INFO
```

## 실행 방법

### 1단계: 스키마 생성

Supabase에 garden6 스키마와 테이블을 생성합니다:

```bash
python create_schema.py
```

이 스크립트는:
- garden6 스키마 생성
- slack_messages 테이블 생성
- 필요한 인덱스 생성
- commit_messages 뷰 생성
- RLS(Row Level Security) 정책 설정

### 2단계: 데이터 마이그레이션

MongoDB 덤프 데이터를 Supabase로 마이그레이션합니다:

```bash
python migrate_to_supabase.py
```

이 스크립트는:
- BSON 파일에서 데이터 읽기
- 타임스탬프 형식 변환
- 배치 단위로 데이터 삽입 (기본 1000개씩)
- 중복 데이터 자동 스킵 (ON CONFLICT DO NOTHING)

## 파일 구조

```
archive/migration/
├── README.md                    # 이 파일
├── requirements.txt             # Python 패키지 의존성
├── migration_config.yaml.sample # 설정 파일 템플릿
├── migration_config.yaml        # 실제 설정 파일 (gitignore 권장)
├── supabase_schema.sql         # 스키마 DDL
├── create_schema.py            # 스키마 생성 스크립트
└── migrate_to_supabase.py      # 데이터 마이그레이션 스크립트
```

## 데이터베이스 스키마

### slack_messages 테이블
- `id`: UUID (Primary Key)
- `ts`: VARCHAR(20) - Slack 타임스탬프 (Unique)
- `ts_for_db`: TIMESTAMP - PostgreSQL 타임스탬프
- `bot_id`: VARCHAR(20)
- `type`: VARCHAR(20)
- `text`: TEXT
- `user`: VARCHAR(20)
- `team`: VARCHAR(20)
- `bot_profile`: JSONB
- `attachments`: JSONB
- `created_at`: TIMESTAMP

### 인덱스
- `idx_ts_for_db_range`: 시간 범위 조회용
- `idx_attachments_author`: 첨부파일 작성자 조회용
- `idx_author_names`: GitHub 사용자명 조회용

### commit_messages 뷰
GitHub 커밋 정보를 쉽게 조회하기 위한 뷰

## 문제 해결

### BSON 파일을 찾을 수 없음
- `migration_config.yaml`의 `bson_file_path`가 올바른지 확인
- 파일 경로가 절대 경로인지 확인

### 스키마가 이미 존재함
- `create_schema.py` 실행 시 기존 스키마 삭제 여부를 묻습니다
- 'y'를 입력하면 기존 스키마를 삭제하고 새로 생성

### 연결 실패
- Supabase 연결 정보가 올바른지 확인
- 네트워크 연결 상태 확인
- SSL이 필요한 경우 자동으로 설정됨

## 주의사항

1. **비밀번호 보안**: `migration_config.yaml` 파일에는 실제 비밀번호가 포함되므로 git에 커밋하지 마세요
2. **데이터 크기**: 대용량 데이터의 경우 시간이 오래 걸릴 수 있습니다
3. **중복 처리**: 기본적으로 중복 데이터는 무시됩니다 (ON CONFLICT DO NOTHING)

## MongoDB에서 새로운 덤프 생성하기

필요한 경우 MongoDB에서 직접 덤프를 생성할 수 있습니다:

```bash
mongodump --db garden6 --collection slack_messages --out ./mongodb_dump
```