import os
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv(
    "COCKROACH_URL",
    "postgresql://ahmed:p3OjZDFd2pJE-0O9qj0aPQ@complianceai-prod-18493.j77.aws-eu-central-1.cockroachlabs.cloud:26257/defaultdb?sslmode=require&options=--cluster%3Dcomplianceai-prod-18493"
)

db_pool = None

def init_pool():
    global db_pool
    if db_pool is None:
        db_pool = SimpleConnectionPool(minconn=1, maxconn=20, dsn=DATABASE_URL)
    return db_pool

def get_db_connection():
    pool = init_pool()
    return pool.getconn()

def release_db_connection(conn):
    if db_pool:
        db_pool.putconn(conn)

def execute_query(query, params=None, fetch_one=False):
    conn = get_db_connection()
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, params or ())
        
        if fetch_one:
            result = cursor.fetchone()
            return dict(result) if result else None
        else:
            results = cursor.fetchall()
            return [dict(row) for row in results]
    except Exception as e:
        print(f"Database query error: {e}")
        raise
    finally:
        cursor.close()
        release_db_connection(conn)
