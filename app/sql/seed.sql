--- Seed Sql For Trace

CREATE TABLE IF NOT EXISTS agent_logs (
    trace_id        UUID PRIMARY KEY,
    session_id      TEXT,
    user_query      TEXT,
    selected_agent  TEXT,
    routing_reason  TEXT,
    agent_content   TEXT,
    final_response  TEXT,
    guardrail_flags TEXT[],
    latency_ms      JSONB,
    error           TEXT,
    created_at      TIMESTAMPTZ DEFAULT now()
);