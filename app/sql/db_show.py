from app.sql.db_seed import get_connections_params
import psycopg
from app.core.logger import logger
from app.config.setting import settings
import sys

def run_db_show():
    if not settings.postgres_dsn():
        logger.error(f"Please setup DB params!...")
        sys.exit(1)
    try:
        with psycopg.connect(settings.postgres_dsn(),connect_timeout=10) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                SELECT jsonb_pretty(jsonb_agg(to_jsonb(t)))
                FROM agent_logs t;
                """)
                result = cur.fetchall()
                if result:
                    for i,value in enumerate(result):
                        print(f"Result-{i} -> {value}")
                
    except psycopg.OperationalError as e:
        logger.error(f"Fetching error -> {e}")



if __name__=="__main__":
    run_db_show()