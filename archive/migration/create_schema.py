#!/usr/bin/env python3
"""
Garden6 Supabase 스키마 생성 스크립트

설정 파일에서 연결 정보를 읽어 Supabase에 스키마와 테이블을 생성합니다.
"""
import psycopg2
import os
import configparser
import logging
import sys

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_config():
    """설정 파일 로드"""
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'migration_config.ini')
    
    if not os.path.exists(config_path):
        logger.error(f"설정 파일을 찾을 수 없습니다: {config_path}")
        logger.info("migration_config.ini.sample을 migration_config.ini로 복사하고 설정을 입력하세요.")
        sys.exit(1)
    
    config.read(config_path)
    return config

def create_connection(config):
    """PostgreSQL 연결 생성"""
    try:
        db_config = {
            'database': config.get('SUPABASE', 'DATABASE'),
            'host': config.get('SUPABASE', 'HOST'),
            'port': config.getint('SUPABASE', 'PORT'),
            'user': config.get('SUPABASE', 'USER'),
            'password': config.get('SUPABASE', 'PASSWORD'),
            'sslmode': 'require',
            'gssencmode': 'disable'
        }
        
        conn = psycopg2.connect(**db_config)
        logger.info(f"PostgreSQL 연결 성공: {db_config['host']}")
        return conn
    except Exception as e:
        logger.error(f"연결 오류: {e}")
        return None

def read_schema_sql():
    """SQL 스키마 파일 읽기"""
    schema_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'supabase_schema.sql')
    
    if not os.path.exists(schema_file):
        logger.error(f"스키마 파일을 찾을 수 없습니다: {schema_file}")
        return None
    
    with open(schema_file, 'r', encoding='utf-8') as f:
        return f.read()

def create_schema():
    """Supabase에 스키마 생성"""
    print("=== Garden6 Supabase 스키마 생성 ===\n")
    
    # 설정 로드
    config = load_config()
    schema_name = config.get('SUPABASE', 'SCHEMA', fallback='garden6')
    
    # DB 연결
    print("1. PostgreSQL 연결 중...")
    conn = create_connection(config)
    if not conn:
        print("   ❌ 연결 실패!")
        return
    
    cur = conn.cursor()
    
    try:
        # 스키마 존재 여부 확인
        print(f"\n2. 기존 {schema_name} 스키마 확인...")
        cur.execute(f"SELECT schema_name FROM information_schema.schemata WHERE schema_name = '{schema_name}'")
        exists = cur.fetchone()
        
        if exists:
            response = input(f"   ⚠️  {schema_name} 스키마가 이미 존재합니다. 삭제하고 다시 생성하시겠습니까? (y/N): ")
            if response.lower() != 'y':
                print("   취소되었습니다.")
                return
            
            # 스키마 삭제
            print(f"\n3. 기존 {schema_name} 스키마 삭제 중...")
            cur.execute(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE")
            conn.commit()
            print("   ✅ 삭제 완료")
        
        # SQL 스크립트 읽기
        print("\n4. 스키마 SQL 파일 읽기...")
        schema_sql = read_schema_sql()
        if not schema_sql:
            return
        
        # 스키마 생성
        print(f"\n5. {schema_name} 스키마 및 테이블 생성 중...")
        cur.execute(schema_sql)
        conn.commit()
        print("   ✅ 생성 완료")
        
        # 생성된 객체 확인
        print(f"\n6. 생성된 객체 확인...")
        
        # 테이블 확인
        cur.execute(f"""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = '{schema_name}' 
            AND table_type = 'BASE TABLE'
        """)
        tables = cur.fetchall()
        print(f"   - 테이블: {', '.join([t[0] for t in tables])}")
        
        # 뷰 확인
        cur.execute(f"""
            SELECT table_name 
            FROM information_schema.views 
            WHERE table_schema = '{schema_name}'
        """)
        views = cur.fetchall()
        if views:
            print(f"   - 뷰: {', '.join([v[0] for v in views])}")
        
        # 인덱스 확인
        cur.execute(f"""
            SELECT indexname 
            FROM pg_indexes 
            WHERE schemaname = '{schema_name}'
            AND indexname NOT LIKE '%_pkey'
        """)
        indexes = cur.fetchall()
        if indexes:
            print(f"   - 인덱스: {', '.join([i[0] for i in indexes])}")
        
        print(f"\n✅ {schema_name} 스키마가 성공적으로 생성되었습니다!")
        print("\n다음 단계:")
        print("1. migration_config.ini 파일을 확인하세요")
        print("2. python migrate_to_supabase.py 를 실행하여 데이터를 마이그레이션하세요")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    create_schema()