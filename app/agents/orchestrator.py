from app.graph.state import AgentState
from langchain_core.prompts import PromptTemplate
from app.service.llm_service import get_openaillm
from app.core.logger import logger
from app.config.prompt_setting import get_prompts

agent_prompt = get_prompts.prompt
base_prompt = agent_prompt["agent_validation"]

_CLASSIFY_PROMPT = """
{base_prompt}
Questions:{Questions}
Category:
"""

async def orchestrator_node(state:AgentState)->dict:
    emit = state["emit"]
    query = state["user_query"]
    prompt_template = PromptTemplate.from_template(_CLASSIFY_PROMPT)
    # chain = prompt_template | get_openaillm()
    # decision = chain.invoke({"Questions":query , "base_prompt":base_prompt })
    # llm_answer = decision.content.strip().lower()
    llm_answer = "Knowledge"
    
    # Orchestrator to set AI Agent

    if "Knowledge" in llm_answer:
        selected = "knowledge"
    elif "sql" in llm_answer:
        selected = "sql"
    elif "research" in llm_answer:
        selected = "research"
    else:
        selected = "research"

    if emit:
        await emit("agent_selected",selected,f"Routing to {selected} agent")

    logger.info(f"Orchestrator router to ->{selected}(LLM decision:{selected})")
    return {
        "selected_agent":selected,
        "routing_reason":f"LLM classified query as {selected}"
    }

def routing_agent(state:AgentState)->str:
    if state.get("guardrail_blocked"):
        return "blocked"
    return state.get("selected_agent","research")