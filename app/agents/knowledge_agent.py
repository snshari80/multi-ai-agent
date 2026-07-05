from app.graph.state import AgentState
import time
import asyncio
from app.service.opensearch_service import get_retriever
from app.core.logger import logger
from langchain_core.prompts import ChatPromptTemplate
from app.config.prompt_setting import get_prompts
from app.service.llm_service import get_bedrockllm

agent_prompt = get_prompts.prompt
base_prompt = agent_prompt["knowledge_agent_prompt"]


_SYNTHESIS_PROMPT = """
{base_prompt}

Retrieved context:
{context}

Question: {question}

Answer:"""

async def knowledge_agent_node(state:AgentState):
    start_time = time.time()
    emit = state.get("emit")
    query = state.get("user_query")

    if emit:
        await emit("agent_process","knowledge_agent" ,f"Search for internal knowledge base")

    try:
        retriever = await asyncio.to_thread(get_retriever)
        chunks = await asyncio.to_thread(retriever.search, query)
    
    except Exception as e:
        logger.error(f"Error While fetching and embedding the query -> {e}")
        return {
            "knowledge_output" : { "error":{e} , "chunks" : []},
            "agent_result": {
                "agent":"knowledge",
                "content":"I couldn't be able to reach the knowledge base",
                "source":[],
                "raw":{ "error" : str(e)}
            },
             "error" : str(e)
        }

    if emit:
        await emit("agent_progress","knowledge",f"Found {len(chunks)} relevant documents, composing the answer.....")

    if not chunks:
        result_content = "I don't have any relevant documents matching this question"
        return {
            "knowledge_output" : { "chunks" : []},
            "agent_result": {
                "agent":"knowledge",
                "content":result_content,
                "source":[],
                "raw":{ "chunks" : []}
            },
            "latency_ms": { **state.get("latency_ms"),"knowledge":time.time() - start_time *1000}
        }

    content_block = "\n\n --- \n\n".join(
        f"[Source: {c["file_name"]}]\n{c["content"]}"
        for c in chunks
    )

    prompt = ChatPromptTemplate.from_template(_SYNTHESIS_PROMPT)
    chain = prompt | get_bedrockllm()
    response = await asyncio.to_thread(chain.invoke, { "question" : query, "context" : content_block, "base_prompt":base_prompt})

    sources = list({c["file_name"] for c in chunks if c["file_name"]})
    latency = time.time() - start_time * 1000

    return {
        "knowledge_output" : { "chunks" : chunks , "answer" : response.content},
        "agent_result":{
            "agent": "knowledge",
            "content" : response.content,
            "sources" : sources,
            "raw" : { "chunks_count" : len(chunks)}
        },
        "latency_ms": { **state.get("latency_ms",{}), "knowledge" :latency},
    }