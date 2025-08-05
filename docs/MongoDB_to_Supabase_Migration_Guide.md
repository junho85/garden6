# Garden6 프로젝트 MongoDB → PostgreSQL/Supabase 전환 가이드

## 목차
1. [개요](#개요)
2. [주요 변경사항](#주요-변경사항)
3. [코드 수정 내역](#코드-수정-내역)
4. [데이터베이스 쿼리 변경 패턴](#데이터베이스-쿼리-변경-패턴)
5. [새로 추가된 파일](#새로-추가된-파일)
6. [의존성 변경](#의존성-변경)
7. [마이그레이션 프로세스](#마이그레이션-프로세스)
8. [보안 및 성능 개선사항](#보안-및-성능-개선사항)

## 개요

Garden6 프로젝트는 Slack 메시지 데이터 저장소를 MongoDB에서 PostgreSQL/Supabase로 성공적으로 전환했습니다. 이 문서는 유사한 전환 작업을 수행하는 다른 프로젝트에서 참고할 수 있도록 주요 변경사항과 패턴을 정리한 것입니다.

### 전환 배경
- **기존**: MongoDB (NoSQL, 문서 기반)
- **신규**: PostgreSQL/Supabase (관계형 DB + JSONB)
- **목적**: ACID 특성 확보, 관계형 데이터 처리 강화, 관리형 서비스 활용

## 주요 변경사항

### 1. 데이터베이스 연결 클래스 변경
- `MongoTools` → `DBTools`
- `pymongo.MongoClient` → `psycopg2.connect`

### 2. 데이터 저장 구조
- MongoDB 컬렉션 → PostgreSQL 테이블
- 동적 문서 구조 → JSONB 타입 활용
- `_id` (ObjectId) → `id` (UUID)

### 3. 쿼리 방식
- MongoDB 쿼리 → SQL + JSONB 연산자
- 중첩 문서 검색 → JSONB 경로 표현식

## 코드 수정 내역

### 1. 데이터베이스 연결 클래스

#### 기존 MongoDB 연결 (MongoTools)
```python
import pymongo

class MongoTools:
    def __init__(self):
        config = configparser.ConfigParser()
        config.read('config.ini')
        self.mongo_host = config['MONGO']['HOST']
        self.mongo_port = config['MONGO']['PORT']
        self.mongo_database = config['MONGO']['DATABASE']
        self.mongo_collection_slack_message = config['MONGO']['COLLECTION_SLACK_MESSAGE']
    
    def connect_mongo(self):
        return pymongo.MongoClient(f"mongodb://{self.mongo_host}:{self.mongo_port}")
    
    def get_database(self):
        conn = self.connect_mongo()
        return conn.get_database(self.mongo_database)
    
    def get_collection(self):
        db = self.get_database()
        return db.get_collection(self.mongo_collection_slack_message)
```

#### 신규 PostgreSQL 연결 (DBTools)
```python
import psycopg2
from psycopg2.extras import RealDictCursor

class DBTools:
    def __init__(self):
        config = configparser.ConfigParser()
        config.read('config.ini')
        self.pg_database = config['POSTGRES']['DATABASE']
        self.pg_host = config['POSTGRES']['HOST']
        self.pg_port = config['POSTGRES']['PORT']
        self.pg_user = config['POSTGRES']['USER']
        self.pg_password = config['POSTGRES']['PASSWORD']
        self.pg_schema = config['POSTGRES']['SCHEMA']
    
    def connect_db(self):
        """PostgreSQL 연결 생성"""
        return psycopg2.connect(
            host=self.pg_host,
            port=self.pg_port,
            database=self.pg_database,
            user=self.pg_user,
            password=self.pg_password,
            sslmode='require',
            gssencmode='disable'
        )
    
    def get_cursor(self, dict_cursor=True):
        """커서 획득 (딕셔너리 형태로 반환 옵션)"""
        conn = self.connect_db()
        if dict_cursor:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
        else:
            cursor = conn.cursor()
        
        # 스키마 설정
        cursor.execute(f"SET search_path TO {self.pg_schema}")
        return conn, cursor
```

### 2. 메인 애플리케이션 수정 (garden.py)

#### 임포트 및 초기화 변경
```python
# 기존
from attendance.mongo_tools import MongoTools

class Garden:
    def __init__(self):
        self.mongo_tools = MongoTools()

# 신규
from attendance.db_tools import DBTools

class Garden:
    def __init__(self):
        self.db_tools = DBTools()
```

## 데이터베이스 쿼리 변경 패턴

### 1. 데이터 조회 (SELECT)

#### MongoDB 방식
```python
# 특정 사용자의 메시지 조회
mongo_collection = self.mongo_tools.get_collection()
for message in mongo_collection.find({"attachments.author_name": user}).sort("ts", 1):
    print(message)

# 시간 범위 조회
for message in mongo_collection.find({
    "ts_for_db": {
        "$gte": datetime.fromtimestamp(oldest),
        "$lt": datetime.fromtimestamp(latest)
    }
}):
    print(message)
```

#### PostgreSQL 방식
```python
# 특정 사용자의 메시지 조회
filters = {'author_name': user}
messages = self.db_tools.find_slack_messages(filters=filters, sort_by="ts")
for message in messages:
    print(dict(message))

# 시간 범위 조회
filters = {
    'ts_for_db_gte': datetime.fromtimestamp(oldest),
    'ts_for_db_lt': datetime.fromtimestamp(latest)
}
messages = self.db_tools.find_slack_messages(filters=filters)
```

#### DBTools의 find_slack_messages 메서드
```python
def find_slack_messages(self, filters=None, sort_by="ts_for_db", limit=None):
    """Slack 메시지 조회"""
    query = "SELECT * FROM slack_messages"
    params = []
    
    if filters:
        where_conditions = []
        for key, value in filters.items():
            if key == 'author_name':
                # JSONB에서 author_name 검색
                where_conditions.append("attachments->0->>'author_name' = %s")
                params.append(value)
            elif key == 'ts_for_db_gte':
                where_conditions.append("ts_for_db >= %s")
                params.append(value)
            elif key == 'ts_for_db_lt':
                where_conditions.append("ts_for_db < %s")
                params.append(value)
            else:
                where_conditions.append(f"{key} = %s")
                params.append(value)
        
        if where_conditions:
            query += " WHERE " + " AND ".join(where_conditions)
    
    if sort_by:
        query += f" ORDER BY {sort_by}"
    
    if limit:
        query += f" LIMIT {limit}"
    
    return self.execute_query(query, params)
```

### 2. 데이터 삽입 (INSERT)

#### MongoDB 방식
```python
try:
    mongo_collection.insert_one(message)
except pymongo.errors.DuplicateKeyError as err:
    print(err)
    continue
```

#### PostgreSQL 방식
```python
import json

try:
    # PostgreSQL에 메시지 삽입
    insert_query = """
        INSERT INTO slack_messages (ts, ts_for_db, bot_id, type, text, "user", team, bot_profile, attachments)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (ts) DO NOTHING
    """
    
    params = (
        message.get('ts'),
        message.get('ts_for_db'),
        message.get('bot_id'),
        message.get('type'),
        message.get('text'),
        message.get('user'),
        message.get('team'),
        json.dumps(message.get('bot_profile')) if message.get('bot_profile') else None,
        json.dumps(message.get('attachments')) if message.get('attachments') else None
    )
    
    self.db_tools.execute_query(insert_query, params, fetch_all=False)
except Exception as err:
    print(err)
    continue
```

### 3. 데이터 삭제 (DELETE)

#### MongoDB 방식
```python
mongo_collection.remove()  # 모든 문서 삭제
```

#### PostgreSQL 방식
```python
delete_query = "DELETE FROM slack_messages"
self.db_tools.execute_query(delete_query, fetch_all=False)
```

### 4. JSONB 데이터 접근

#### Python에서 JSONB 데이터 처리
```python
# PostgreSQL에서 가져온 메시지의 attachments 처리
for message in messages:
    # JSONB 필드는 자동으로 Python dict/list로 변환됨
    attachments = message["attachments"] if message["attachments"] else []
    
    for attachment in attachments:
        author_name = attachment.get("author_name")
        commit_text = attachment.get("text")
        repository = attachment.get("footer")
```

#### SQL에서 JSONB 쿼리
```sql
-- 특정 author_name을 가진 메시지 찾기
SELECT * FROM slack_messages 
WHERE attachments @> '[{"author_name": "junho85"}]';

-- 첫 번째 attachment의 author_name 가져오기
SELECT attachments->0->>'author_name' as author 
FROM slack_messages 
WHERE attachments IS NOT NULL;

-- 모든 attachments를 펼쳐서 조회
SELECT 
    sm.ts,
    attachment->>'author_name' as author,
    attachment->>'text' as commit_message
FROM 
    slack_messages sm,
    LATERAL jsonb_array_elements(sm.attachments) as attachment
WHERE 
    sm.attachments IS NOT NULL;
```

## 새로 추가된 파일

### 1. 데이터베이스 연결 도구
- **`attendance/db_tools.py`**: PostgreSQL 연결 및 쿼리 처리 클래스

### 2. 마이그레이션 관련 파일 (`archive/migration/`)
- **`supabase_schema.sql`**: PostgreSQL 테이블 스키마 정의
- **`create_schema.py`**: 스키마 생성 스크립트
- **`migrate_to_supabase.py`**: MongoDB 데이터를 PostgreSQL로 마이그레이션
- **`migration_config.yaml.sample`**: 마이그레이션 설정 템플릿
- **`requirements.txt`**: 마이그레이션 전용 의존성
- **`README.md`**: 마이그레이션 가이드

### 3. 스키마 정의 (supabase_schema.sql)
```sql
-- 스키마 생성
CREATE SCHEMA IF NOT EXISTS garden6;
SET search_path TO garden6;

-- Slack 메시지 테이블
CREATE TABLE slack_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ts VARCHAR(20) UNIQUE NOT NULL,
    ts_for_db TIMESTAMP NOT NULL,
    bot_id VARCHAR(20),
    type VARCHAR(20),
    text TEXT,
    "user" VARCHAR(20),
    team VARCHAR(20),
    bot_profile JSONB,
    attachments JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX idx_slack_messages_ts ON slack_messages (ts);
CREATE INDEX idx_slack_messages_ts_for_db ON slack_messages (ts_for_db);
CREATE INDEX idx_slack_messages_user ON slack_messages ("user");
CREATE INDEX idx_slack_messages_bot_id ON slack_messages (bot_id);
CREATE INDEX idx_slack_messages_created_at ON slack_messages (created_at);

-- JSONB 인덱스
CREATE INDEX idx_slack_messages_attachments ON slack_messages USING GIN (attachments);
CREATE INDEX idx_slack_messages_bot_profile ON slack_messages USING GIN (bot_profile);

-- 시간 범위 검색 최적화
CREATE INDEX idx_slack_messages_ts_for_db_range ON slack_messages (ts_for_db);

-- author_name 검색 최적화
CREATE INDEX idx_slack_messages_author_names ON slack_messages 
USING GIN ((attachments -> 'author_name'));
```

## 의존성 변경

### requirements.txt 수정
```diff
slackclient==2.9.4
Django>=4.2,<5.0
- pymongo>=4.0.0
+ psycopg2-binary>=2.9.0
PyYAML>=6.0
Markdown>=3.4.0
requests>=2.28.0
```

### 마이그레이션 전용 의존성 (archive/migration/requirements.txt)
```
psycopg2-binary>=2.9.0
pymongo>=4.0.0
pyyaml>=6.0
python-dateutil>=2.8.0
```

## 마이그레이션 프로세스

### 1. MongoDB 데이터 덤프
```bash
# MongoDB 데이터 내보내기
mongodump --collection=slack_messages --out=./20250803_mongodb_dump
```

### 2. PostgreSQL 스키마 생성
```bash
cd archive/migration
python create_schema.py
```

### 3. 데이터 마이그레이션
```bash
python migrate_to_supabase.py
```

### 4. 설정 파일 업데이트
```ini
# config.ini 수정
[POSTGRES]
DATABASE = your-database
HOST = your-host.supabase.co
PORT = 5432
USER = your-user
PASSWORD = your-password
SCHEMA = garden6
```

## 보안 및 성능 개선사항

### 1. 보안 강화
- **SSL 연결**: `sslmode='require'`로 암호화된 연결 강제
- **RLS 정책**: Row Level Security로 세밀한 권한 관리
- **환경 변수**: 민감한 정보는 환경 변수로 관리

### 2. 성능 최적화
- **인덱스**: 자주 조회되는 필드에 인덱스 생성
- **JSONB GIN 인덱스**: 동적 데이터 검색 성능 향상
- **배치 처리**: 대량 데이터 삽입 시 배치 처리
- **ON CONFLICT**: 중복 처리로 불필요한 에러 방지

### 3. 운영 효율성
- **트랜잭션**: ACID 특성으로 데이터 일관성 보장
- **백업/복원**: Supabase의 자동 백업 기능 활용
- **모니터링**: PostgreSQL 표준 모니터링 도구 활용 가능

## 주의사항 및 팁

### 1. JSONB vs JSON
- `JSONB`: 바이너리 형식, 인덱싱 가능, 중복 키 제거
- `JSON`: 텍스트 형식, 입력 순서 유지
- 대부분의 경우 `JSONB` 사용 권장

### 2. 타임스탬프 처리
```python
# Slack 타임스탬프를 PostgreSQL TIMESTAMP로 변환
def format_timestamp(ts_string):
    try:
        ts_float = float(ts_string)
        return datetime.fromtimestamp(ts_float)
    except:
        return None
```

### 3. 에러 처리
```python
# PostgreSQL 특정 에러 처리
try:
    cursor.execute(query, params)
except psycopg2.IntegrityError as e:
    if 'duplicate key' in str(e):
        # 중복 키 처리
        pass
    else:
        raise
```

### 4. 커넥션 풀링
```python
# 프로덕션 환경에서는 커넥션 풀 사용 권장
from psycopg2 import pool

connection_pool = psycopg2.pool.SimpleConnectionPool(
    1, 20,  # 최소 1개, 최대 20개 연결
    host=host,
    database=database,
    user=user,
    password=password
)
```

## 결론

MongoDB에서 PostgreSQL/Supabase로의 전환은 다음과 같은 이점을 제공합니다:

1. **데이터 일관성**: ACID 특성으로 트랜잭션 보장
2. **유연성**: JSONB로 NoSQL의 유연성 유지
3. **성능**: 인덱싱과 쿼리 최적화로 향상된 성능
4. **관리 편의성**: Supabase의 관리형 서비스 활용
5. **생태계**: PostgreSQL의 풍부한 도구와 확장 기능

이 가이드가 유사한 마이그레이션 프로젝트에 도움이 되기를 바랍니다.