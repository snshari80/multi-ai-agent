from langgraph.graph import StateGraph, START, END
from app.graph.state import AgentState
from app.core.utils import (guardrail_type, agents_type)
from app.core.logger import logger
from app.agents.orchestrator import (routing_agent,orchestrator_node)
from app.guardrail.guardrail import run_input_guardrail
from app.agents.research_agent import research_agent_node
from app.agents.author_agent import author_agent_node
from app.evaluation.evaluator import evaluator_node
from app.agents.knowledge_agent import knowledge_agent_node



async def guardrail_input_node(state:AgentState) -> dict:
    emit = state.get("emit")
    result = run_input_guardrail(state["user_query"])
    if result["guardrail_blocked"] and emit:
        await emit("guardrail_blocked","guardrail", "Your request has been blocked by guardrail")
    return result

# Blocked Response:
async def blocked_response(state:AgentState)->dict:
    return {
        "agent_result":{
            "agent":"guardrail",
            "content": "Your request has been blocked due to guardrail policies",
            "source":[],
        },
        "final_response":"This request was blocked for security reasons "
                          "(possible SQL injection detected).",
    }

_compiler_graph = None

def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("guardrail_input",guardrail_input_node)
    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("knowledge",knowledge_agent_node)
    # graph.add_node("sql")
    graph.add_node("research", research_agent_node)
    graph.add_node("author",author_agent_node)
    graph.add_node("evaluator", evaluator_node)
    graph.add_node("blocked",blocked_response)

    graph.add_edge(START,"guardrail_input")

    def check_guardrail_status(state:AgentState) ->str:
        return "blocked" if state.get("guardrail_blocked") else "orchestrator"

    graph.add_conditional_edges(
        "guardrail_input",
        check_guardrail_status,
        guardrail_type
    )

    graph.add_conditional_edges(
        "orchestrator",
        routing_agent,
        agents_type
    )

    graph.add_edge("knowledge" , "author")
    graph.add_edge("research","author")
    # graph.add_edge("sql", "author")

    graph.add_edge("author","evaluator")
    graph.add_edge("blocked", "evaluator")

    graph.add_edge("evaluator",END)

    compiled = graph.compile()
    logger.info(f"LangGraph compiled successfully")
    return compiled

def get_graph():
    global _compiler_graph
    if _compiler_graph is None:
        _compiler_graph = build_graph()
    return _compiler_graph