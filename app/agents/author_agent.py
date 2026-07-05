from app.graph.state import AgentState
import time
from app.core.logger import logger 
from app.guardrail.guardrail import masking_pii
from langchain_core.prompts import ChatPromptTemplate
from app.config.prompt_setting import get_prompts
from app.service.llm_service import get_bedrockllm
import asyncio

agent_prompt = get_prompts.prompt
base_prompt = agent_prompt["author_agent_prompt"]

_SYNTHESIS_PROMPT = """
{base_prompt}

User's original question: {question}

Draft answer from {agent} agent:
{draft}

Polished final answer:"""

async def author_agent_node(state:AgentState):
    start_time = time.time()
    emit = state.get("emit")
    question = state.get("user_query")
    agent_result = state.get("agent_result",{})

    draft = agent_result.get("content","")
    source_agent = agent_result.get("agent","unknown")
    sources = agent_result.get("sources",[])

    if emit:
        await emit("agent_progress", "author", "composing final response....")
        logger.info("Composing final answers.")

    print(f"draft ->{draft}")
    if draft and not draft.lower().startswith(("i coundn't" )):
        prompt = ChatPromptTemplate.from_template(_SYNTHESIS_PROMPT)
        chain = prompt | get_bedrockllm()
        polishd = (
            await asyncio.to_thread(chain.invoke , {
                "question":question,
                "agent" : source_agent,
                "draft": draft,
                "base_prompt" : base_prompt
            })
        ).content()
    else:
        polishd = draft

    masked_response, pii_found = masking_pii(polishd)

    if emit:
        await emit("agent_complete","author","Response ready" , data={
            "response": masked_response,
            "source_agent":source_agent,
            "sources":sources
        })
    latency = (time.time() - start_time)*1000
    logger.info(f"Author Process Completed ->{latency} ms")
    return {
        "final_response" : masked_response,
        "guardrail_flags": state.get("guardrail_flags"),
        "latency":{**state.get("latency_ms",{}),"author":latency}
    }