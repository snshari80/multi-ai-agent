from langchain_classic.memory import ConversationBufferMemory
from langchain_core.prompts import PromptTemplate
import asyncio

memory_store = {}

def get_memory(sessionid:str):
    if sessionid not in memory_store:
        memory_store[sessionid] = ConversationBufferMemory(return_messages=True)
    return memory_store[sessionid]

async def rewrite_query_with_context(messages,query,llm):
    histoty_text = "\n".join(
        f"{'User' if m.type == "human" else 'AI'}:{m.content}"
        for m in messages[-5:]
    )
    prompt ="""
    You are a query rewriting assistanct.

    Conversion:
    {history}

    Current Question:
    {query}

    Rewrite the question to be fully self-contained.
    Only return the rewritten query.
    """
    prompt_template = PromptTemplate.from_template(prompt)
    chain = prompt_template | llm
    response = await asyncio.to_thread(chain.invoke,{"history":histoty_text , "query":query })
    if response.content:
        return response.content
    else:
        return response
