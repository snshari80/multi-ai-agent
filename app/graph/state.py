from typing import TypedDict,Optional,Callable,Awaitable
from typing_extensions import NotRequired

class AgentState(TypedDict):
    # User Related 
    session_id:str
    user_query:str
    # Event Emit 
    emit:NotRequired[Callable[...,Awaitable]]
    # Guardrail with user query
    guardrail_blocked:NotRequired[bool]
    guardrail_flags:NotRequired[list[str]]
    # Routing for user query
    selected_agent:NotRequired[str]
    routing_reason:NotRequired[str]
    detected_org:NotRequired[str]
    # Agent Output
    knowledge_output:NotRequired[dict]
    sql_output:NotRequired[dict]
    research_output:NotRequired[dict]
    # Author Agent output
    agent_result:NotRequired[dict]
    # Final response to user
    final_response:NotRequired[dict]
    #tracking the event
    trace_id:NotRequired[str]
    latency_ms:NotRequired[str]
    error:NotRequired[Optional[str]]

def new_state(session_id:str,user_query:str,emit=None) -> AgentState:
    return AgentState(
        session_id=session_id,
        user_query=user_query,
        emit=emit,
        guardrail_blocked=False,
        guardrail_flags=[],
        detected_org=None,
        latency_ms={},
        error=None,
    )
