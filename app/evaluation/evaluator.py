from app.graph.state import AgentState
from app.config.setting import settings
from app.core.logger import logger
import uuid
from datetime import datetime, timezone
import psycopg
from psycopg.types.json import Json
import os
from dotenv import load_dotenv
from pathlib import Path

_PARENT_PATH = Path(__file__).parent
_ENV_PATH = _PARENT_PATH.parent/".ENV"

load_dotenv(_ENV_PATH)

_evl_cfg = settings.evaluation
_table_name = _evl_cfg.get("table_name","")

def capture_trace(state:AgentState):
    if not _evl_cfg.get("enabled", False):
        logger.info(f"Evaluator isn't enabled ->{_evl_cfg["enabled"]}")
        return ""
    
    trace_id = str(uuid.uuid4())
    agent_result = state.get("agent_result",{})

    trace = {
        "trace_id" : trace_id,
        "session_id" : trace_id,
        "user_query": state.get("user_query",""),
        "selected_agent":state.get("selected_agent",""),
        "routing_reason":state.get("routing_reason",""),
        "agent_content":agent_result.get("content", ""),
        "final_response":state.get("final_response",{}),
        "guardrail_flags":state.get("guardrail_flags",[]),
        "latency_ms":state.get("latency_ms",""),
    }

    # cloud watch

    if _evl_cfg.get("cloudwatch_log",True):
        cw_line = { "Eval_Trace":trace , "Timestamp": datetime.now(timezone.utc).isoformat()}
        print(f"cw_line - >{cw_line}")
    
    if _evl_cfg.get("store") == "postgres":
        try:
            with psycopg.connect(settings.postgres_dsn(), connect_timeout=10) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"""
                        INSERT INTO {_table_name}
                        ( trace_id, session_id, user_query, selected_agent, routing_reason, agent_content, final_response, guardrail_flags, latency_ms)
                        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        """,
                        (
                            trace["trace_id"],
                            trace["session_id"],
                            trace["user_query"],
                            trace["selected_agent"],
                            trace["routing_reason"],
                            trace["agent_content"],
                            Json(trace["final_response"]),
                            trace["guardrail_flags"],
                            Json(trace["latency_ms"],)
                        )
                    )
                conn.commit()
            logger.info(f"Trace Captured -> {trace_id[:8]} and persisted to postgres")
        except Exception as e:
            logger.error(f"Failed to persist trace to PostgreSQL: {e}")
    
    return trace_id
    


async def evaluator_node(state:AgentState):
    emit = state.get("emit")
    trace_id = capture_trace(state)

    if emit and trace_id:
        await emit("eval_captured", "evaluator", "Response logged for evalution", data={"trace_id":trace_id})
    
    return {"trace_id":trace_id}