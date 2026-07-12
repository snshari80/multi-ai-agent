from app.core.logger import logger
from app.graph.state import AgentState
import time
from app.config.setting import settings
from app.config.prompt_setting import get_prompts
import asyncio
from app.service.google_service import (google_search_service, read_url)
from app.service.llm_service import get_openaillm
from langchain_core.prompts import PromptTemplate
from app.service.memory_service import rewrite_query_with_context

agent_prompt = get_prompts.prompt
base_prompt = agent_prompt["research_agent_prompt"]


_SYNTHESIS_PROMPT = """
{base_prompt}

Sources:
{sources}
Question:{questions}
Answer:
"""


async def research_agent_node(state:AgentState):
    start_time = time.time()
    emit = state.get("emit")
    query = state.get("user_query")
    max_urls = settings.research["max_urls_to_read"]
    message = state.get("messages")

    if emit:
        await emit("agent_progress","research","Searching the web.....")

    llm = get_openaillm()

    rewrite_query = await rewrite_query_with_context(message,query,llm)

    search_result = await google_search_service(rewrite_query)

    if not search_result:
        return {
            "research_output":{"results":[]},
            "agent_result":{
                "agent":"research",
                "content":"I couldn't find any web results for this question.",
            },
            "latency_ms":{
                **state.get("latency_ms",{}),
                "research" : (time.time() - start_time)*1000,
            }
        }

    urls_to_read = search_result[:max_urls]
    read_pages = []
    for i, read in enumerate(urls_to_read,start=1):
        if emit:
            await emit("agent_progress" , "research" , f"Reading the source {i} of {len(urls_to_read)}")
        page = await asyncio.to_thread(read_url,read["url"])
        if page["success"]:
            read_pages.append(page)

        if not read_pages:
            if emit:
                await emit("agent_progress","research", "Couldn't read full pages, using search snippets...")
        sources_block = "\n\n".join(
            f"[{i}] {r['title']} ({r['url']})\n{r['snippet']}"
            for i, r in enumerate(urls_to_read[:max_urls], start=1)
            )
        source_url = [r["url"] for r in urls_to_read[:max_urls]]
    else:
        sources_block = "\n\n".join(
            f"[{i}] {p["title"]} ({p["url"]})\n{p["text"]}"
            for i,p in enumerate(read_pages,start=1)
        )
        source_url = [p["url"] for p in read_pages]
        

    #Synthesise the answer
    if emit:
        await emit("agent_progress","research","Synthesising answer from sources....")
        logger.info(f"Synthesising answer from sources....")

    prompt_template = PromptTemplate.from_template(_SYNTHESIS_PROMPT)
    chain = prompt_template | get_openaillm()
    response = await asyncio.to_thread(chain.invoke, {"sources":sources_block , "questions":query , "base_prompt":base_prompt })
    latency = int((time.time() - start_time)*1000)

    return {
        "reaserch_output":{
            "search_results":search_result,
            "pages_read":len(read_pages),
        },
        "agent_result":{
            "agent":"research",
            "content": response.content.strip().lower(),
            "sources":source_url
        },
        "latency_ms":{**state.get("latency_ms",{}),"research":f"{latency} ms"}
    }