
from app.graph.state import AgentState
from app.service.sql_service import (frame_query, verify_sql, execute_query)
import time
import asyncio

from app.core.logger import logger
import json
from langchain_core.prompts import ChatPromptTemplate
from app.config.prompt_setting import get_prompts
from app.service.llm_service import get_bedrockllm


SYSTEM_PROMPT = get_prompts.prompt["sql_answer_agent"]

_ANSWER_PROMPT = """The user asked: {question}

The SQL query returned these rows (JSON):
{rows}

{system_prompt}"""

async def sql_agent_node(state:AgentState) ->dict:
        start_time = time.time()
        emit = state.get("emit")
        question = state.get("user_query")

        if emit:
            await emit("agent_progress" , "sql" , "framing SQL QUERY from user question...")
        sql = await asyncio.to_thread(frame_query,question)
        verification = await asyncio.to_thread(verify_sql, sql)
        
        if not verification["valid"]:
              logger.error(f"SQL verfication failed -> {verification["reason"]}")
              content = (
                    "I couldn't run the data request safely."
                    f"Reason:{verification["reason"]}"
              )
              return {
                    "sql_output":{"sql":sql , "verification":False, "reason": verification["reason"]},
                    "agent_result":{
                          "agent":"sql",
                          "content":content,
                          "sources" : [],
                          "raw" : {"sql":sql , "verification" : verification}
                    },
                    "latency_ms":{
                          **state.get("latency_ms",{}), "sql": time.time() - start_time *1000
                    }
              }

        # Excute the query
        if emit:
              await emit("agent_progress","sql","Executing query database....")

        exec_response = await asyncio.to_thread(execute_query,sql)
        
        if not exec_response["success"]:
              content = f"The query failed to execute -> {exec_response["error"]}"
              return {
                    "sql_output": { "sql" : sql, "verfied" : verification["valid"], "execution" : exec_response },
                    "agent_result" : {
                          "agent":"sql",
                          "content":content,
                          "source" : [],
                          "raw" :{ "sql": sql , "error" : exec_response["error"]}
                    },
                    "latency_ms" : {**state.get("latency_ms",{}), "sql" : time.time() - start_time *1000}
              }

        if emit:
              await emit("agent_progress" , "sql" , f"Received rows ->{exec_response["rows_count"]}, composing answer")

        raw_json = json.dumps(exec_response["rows"][:20], default=str)
        prompt = ChatPromptTemplate.from_template(_ANSWER_PROMPT)
        chain = prompt | get_bedrockllm()
        answer = await asyncio.to_thread(chain.invoke,{
              "question" : question,
              "rows":raw_json,
              "system_prompt":SYSTEM_PROMPT
        })
        final_answer = answer.content

        latency = int((time.time() - start_time) *1000)

        return {
              "sql_output":{
                    "sql" : sql,
                    "verified" : verification["valid"],
                    "rows_count" : exec_response["rows_count"],
                },
                "agent_result":{
                      "agent":"sql",
                      "content":final_answer,
                      "sources":[f"sql :{sql}"],
                },
                "latency_ms" : {
                      **state.get("latency_ms",{}), "sql":f"{latency} ms"
                }
        }
