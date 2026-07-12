import os
from pathlib import Path
from dotenv import load_dotenv
from app.core.logger import logger
import sys
import psycopg

_PARENT_PATH = Path(__file__).parent
_ENV_PATH = Path().resolve()/".ENV"
_SEED_SQL = _PARENT_PATH / "seed.sql"

if not _ENV_PATH.exists():
    logger.error(f"Env file missing please set")
    sys.exit(1)

load_dotenv(_ENV_PATH)

def get_connections_params()->dict:
    missings = []
    params = {}
    for key in ("POSTGRES_HOST","POSTGRES_DB","POSTGRES_USER","POSTGRES_PASSWORD"):
        val = os.getenv(key)
        if not val:
            missings.append(key)
        params[key] = val

    if missings:
        logger.exception(f"Please set RDS params ->{missings}")
        sys.exit(1)

    return {
        "dbname":params["POSTGRES_DB"],
        "user":params["POSTGRES_USER"],
        "password":params["POSTGRES_PASSWORD"],
        "host":params["POSTGRES_HOST"],
        "port":int(os.getenv("POSTGRES_PORT", "5432")),
    }

def _ensure_db_exist(params:dict):
    target_db = params["dbname"]

    maintence_params = {**params, "dbname" : "postgres"}
    try:
        with psycopg.connect(**maintence_params,connect_timeout=10,autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (target_db,))
                db_exist = cur.fetchone()
                if db_exist:
                    logger.info(f"DB exist -> {target_db}")
                else:
                    cur.execute(f'CREATE DATABASE "{target_db}"')
                    logger.info(f"DB created now ->{target_db}")

    except psycopg.OperationalError as e:
        logger.exception(f"Error while fetching or creating DB ->{e}")
        sys.exit(1)



def run_db_seed():
    params = get_connections_params()
    if not params:
        logger.error(f"Please setup DB params!...")
        sys.exit(1)
    _ensure_db_exist(params)
    try:
        with psycopg.connect(**params,connect_timeout=10) as conn:
            trace_sql_seed = _SEED_SQL.read_text(encoding="utf-8")
            with conn.cursor() as curs:
                curs.execute("SELECT to_regclass(%s)", ("public.agent_logs",))
                exists = curs.fetchone()[0]
                if exists:
                    logger.info(f"Agent Log table exist skipping creations.....")
                    sys.exit(1)
                else:
                    curs.execute(trace_sql_seed)
                    conn.commit()
                    logger.info(f"Trace Table created -> {params["dbname"]}")        
    except psycopg.OperationalError as e:
        logger.exception(f"Error while fetching or creating DB ->{e}")
        sys.exit(1)
    except psycopg.Error as e:
        print(f"[ERROR] SQL execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_db_seed()