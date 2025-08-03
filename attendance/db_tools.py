import configparser
import os
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor


class DBTools:
    def __init__(self):
        config = configparser.ConfigParser()
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(BASE_DIR, 'config.ini')
        config.read(path)

        # PostgreSQL connection parameters
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

    def execute_query(self, query, params=None, fetch_one=False, fetch_all=True):
        """쿼리 실행 및 결과 반환"""
        conn, cursor = self.get_cursor()
        try:
            cursor.execute(query, params)
            
            if query.strip().upper().startswith('SELECT'):
                if fetch_one:
                    result = cursor.fetchone()
                elif fetch_all:
                    result = cursor.fetchall()
                else:
                    result = None
            else:
                conn.commit()
                result = cursor.rowcount
            
            return result
        finally:
            cursor.close()
            conn.close()

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