from app.graph.state import AgentState
from langchain_core.prompts import PromptTemplate
from app.service.llm_service import get_openaillm
from app.core.logger import logger
from app.config.prompt_setting import get_prompts
from app.config.setting import settings
import time

agent_prompt = get_prompts.prompt
base_prompt = agent_prompt["agent_validation"]
sql_keywords = settings.routing["sql"]

_CLASSIFY_PROMPT = """
{base_prompt}
Questions:{Questions}
Category:
"""

def _check_sql_keywords(query:str) -> bool:
    q_lower = query.lower()
    return any(kw in q_lower for kw in sql_keywords)


async def orchestrator_node(state:AgentState)->dict:
    start_time = time.time()
    emit = state["emit"]
    query = state["user_query"]

    if _check_sql_keywords(query):
        await emit("agent_progress" , "sql" , "Routing to SQL Agent (Identified SQL query in user question)")
        return {
        "selected_agent":"sql",
        "routing_reason":"Query contains data-question keywords"
        }

    prompt_template = PromptTemplate.from_template(_CLASSIFY_PROMPT)
    chain = prompt_template | get_openaillm()
    decision = chain.invoke({"Questions":query , "base_prompt":base_prompt })
    llm_answer = decision.content.strip().lower()

    # Orchestrator to set AI Agent
    if "knowledge" in llm_answer:
        selected = "knowledge"
    elif "sql" in llm_answer:
        selected = "sql"
    elif "research" in llm_answer:
        selected = "research"

    if emit:
        await emit("agent_selected",selected,f"Routing to {selected} agent")
    
    latency_ms = int((time.time() - start_time)*1000)

    logger.info(f"Orchestrator router to ->{selected}(LLM decision:{selected})")
    return {
        "selected_agent":selected,
        "routing_reason":f"LLM classified query as {selected}",
        "latency_ms":{**state.get("latency_ms",{}),"orchestrator": f"{latency_ms} ms"}
    }

def routing_agent(state:AgentState)->str:
    if state.get("guardrail_blocked"):
        return "blocked"
    return state.get("selected_agent","research")