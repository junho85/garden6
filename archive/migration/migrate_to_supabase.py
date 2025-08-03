#!/usr/bin/env python3
"""
Garden6 MongoDB to Supabase Migration Script

이 스크립트는 Garden6의 MongoDB slack_messages 덤프 파일을 
Supabase PostgreSQL로 마이그레이션합니다.
"""
import psycopg2
import bson
import json
from datetime import datetime, timedelta
import os
import logging
import yaml
import sys
from psycopg2.extras import execute_values, RealDictCursor
from typing import List, Dict, Any, Optional

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_config():
    """YAML 설정 파일 로드"""
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'migration_config.yaml')
    
    if not os.path.exists(config_path):
        logger.error(f"설정 파일을 찾을 수 없습니다: {config_path}")
        logger.info("migration_config.yaml.sample을 migration_config.yaml로 복사하고 설정을 입력하세요.")
        sys.exit(1)
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    return config

def get_db_config(config):
    """설정 파일에서 데이터베이스 연결 정보 가져오기"""
    supabase_config = config['supabase']
    return {
        'database': supabase_config['database'],
        'host': supabase_config['host'],
        'port': supabase_config['port'],
        'user': supabase_config['user'],
        'password': supabase_config['password'],
        'sslmode': 'require',
        'gssencmode': 'disable'
    }

def create_connection(db_config, schema_name):
    """PostgreSQL 연결 생성"""
    try:
        conn = psycopg2.connect(**db_config)
        # 스키마 설정
        cursor = conn.cursor()
        cursor.execute(f"SET search_path TO {schema_name}")
        cursor.close()
        logger.info(f"PostgreSQL 연결 성공: {db_config['host']}")
        return conn
    except Exception as e:
        logger.error(f"연결 오류: {e}")
        return None

def read_bson_file(file_path):
    """BSON 파일 읽기"""
    documents = []
    with open(file_path, 'rb') as f:
        while True:
            try:
                # BSON 문서 크기 읽기 (4 bytes)
                size_data = f.read(4)
                if not size_data:
                    break
                
                # 크기 정보를 포함한 전체 문서 읽기
                size = int.from_bytes(size_data, 'little')
                f.seek(-4, 1)  # 4바이트 뒤로
                doc_data = f.read(size)
                
                if doc_data:
                    doc = bson.decode(doc_data)
                    documents.append(doc)
            except Exception as e:
                print(f"문서 읽기 오류: {e}")
                break
    return documents

def format_timestamp(ts_string):
    """Slack 타임스탬프를 PostgreSQL TIMESTAMP로 변환"""
    try:
        ts_float = float(ts_string)
        return datetime.fromtimestamp(ts_float)
    except:
        return None

def prepare_document_for_insert(doc):
    """MongoDB 문서를 PostgreSQL 삽입용으로 변환"""
    ts = doc.get('ts')
    ts_for_db = format_timestamp(ts) if ts else None
    
    if not ts or not ts_for_db:
        return None
    
    return (
        ts,
        ts_for_db,
        doc.get('bot_id'),
        doc.get('type'),
        doc.get('text'),
        doc.get('user'),
        doc.get('team'),
        json.dumps(doc.get('bot_profile')) if doc.get('bot_profile') else None,
        json.dumps(doc.get('attachments')) if doc.get('attachments') else None
    )

def migrate_data():
    """BSON 데이터를 Supabase로 마이그레이션"""
    print("=== Garden6 MongoDB to Supabase 마이그레이션 ===")
    print("이 스크립트는 Garden6의 slack_messages 덤프 파일을 Supabase로 마이그레이션합니다.\n")
    
    # 설정 로드
    config = load_config()
    
    # 로그 레벨 설정
    log_level = config['migration'].get('log_level', 'INFO')
    logging.getLogger().setLevel(getattr(logging, log_level))
    
    # BSON 파일 경로
    bson_file = config['mongodb']['bson_file_path']
    
    # 상대 경로인 경우 현재 스크립트 위치를 기준으로 절대 경로로 변환
    if not os.path.isabs(bson_file):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        bson_file = os.path.join(script_dir, bson_file)
    
    if not os.path.exists(bson_file):
        print(f"❌ BSON 파일을 찾을 수 없습니다: {bson_file}")
        print("   migration_config.yaml의 bson_file_path를 확인해주세요.")
        # 가능한 경로 제안
        script_dir = os.path.dirname(os.path.abspath(__file__))
        possible_paths = [
            os.path.join(script_dir, "20250803_mongodb_dump/slack_messages.bson"),
            os.path.join(script_dir, "mongodb_dump/slack_messages.bson")
        ]
        existing_paths = [p for p in possible_paths if os.path.exists(p)]
        if existing_paths:
            print(f"   다음 경로에서 BSON 파일을 발견했습니다:")
            for path in existing_paths:
                print(f"   - {path}")
        return
    
    # DB 연결 설정 가져오기
    db_config = get_db_config(config)
    schema_name = config['supabase'].get('schema', 'garden6')
    batch_size = config['migration'].get('batch_size', 1000)
    
    print(f"\n설정 정보:")
    print(f"   - BSON 파일: {bson_file}")
    print(f"   - 대상 스키마: {schema_name}")
    print(f"   - 배치 크기: {batch_size}")
    
    print("\n1. BSON 파일 읽기 시작...")
    documents = read_bson_file(bson_file)
    print(f"   - {len(documents)}개의 문서를 읽었습니다.")
    
    print("\n2. PostgreSQL 연결...")
    conn = create_connection(db_config, schema_name)
    if not conn:
        print("   - 연결 실패!")
        return
    
    cur = conn.cursor()
    
    try:
        # 스키마가 존재하는지 확인
        print(f"\n3. {schema_name} 스키마 확인...")
        cur.execute(f"SELECT schema_name FROM information_schema.schemata WHERE schema_name = '{schema_name}'")
        if not cur.fetchone():
            print(f"   - {schema_name} 스키마가 없습니다. create_schema.py를 먼저 실행해주세요.")
            return
        
        # 기존 데이터 개수 확인
        cur.execute(f"SELECT COUNT(*) FROM {schema_name}.slack_messages")
        existing_count = cur.fetchone()[0]
        print(f"   - 기존 데이터: {existing_count}개")
        
        # 데이터 변환 및 준비
        print("\n4. 데이터 변환 중...")
        insert_data = []
        skipped = 0
        
        for doc in documents:
            prepared = prepare_document_for_insert(doc)
            if prepared:
                insert_data.append(prepared)
            else:
                skipped += 1
        
        print(f"   - 변환 완료: {len(insert_data)}개 (스킵: {skipped}개)")
        
        if insert_data:
            print("\n5. 데이터 삽입 중...")
            
            # 배치 삽입 (성능 최적화)
            insert_query = f"""
                INSERT INTO {schema_name}.slack_messages 
                (ts, ts_for_db, bot_id, type, text, "user", team, bot_profile, attachments)
                VALUES %s
                ON CONFLICT (ts) DO NOTHING
            """
            processed_total = 0
            
            for i in range(0, len(insert_data), batch_size):
                batch = insert_data[i:i+batch_size]
                
                # 배치 처리 전 개수 확인
                cur.execute(f"SELECT COUNT(*) FROM {schema_name}.slack_messages")
                count_before = cur.fetchone()[0]
                
                execute_values(cur, insert_query, batch)
                conn.commit()
                
                # 배치 처리 후 개수 확인
                cur.execute(f"SELECT COUNT(*) FROM {schema_name}.slack_messages")
                count_after = cur.fetchone()[0]
                
                batch_inserted = count_after - count_before
                processed_total += len(batch)
                
                print(f"   - 진행률: {processed_total}/{len(insert_data)} (배치 {len(batch)}개 중 {batch_inserted}개 삽입)")
            
            print(f"\n6. 마이그레이션 완료!")
            
            # 최종 데이터 개수 확인
            cur.execute(f"SELECT COUNT(*) FROM {schema_name}.slack_messages")
            final_count = cur.fetchone()[0]
            print(f"   - 최종 데이터 개수: {final_count}개")
            
            # 샘플 데이터 확인
            cur.execute(f"""
                SELECT ts, ts_for_db, text, attachments->0->>'author_name' as author
                FROM {schema_name}.slack_messages 
                WHERE attachments IS NOT NULL 
                LIMIT 5
            """)
            
            print("\n7. 샘플 데이터:")
            for row in cur.fetchall():
                print(f"   - {row[1]}: {row[3]} - {row[2][:50]}...")
        
    except Exception as e:
        print(f"\n오류 발생: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    migrate_data()