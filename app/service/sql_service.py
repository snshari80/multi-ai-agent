
from langchain_core.prompts import ChatPromptTemplate
from app.config.prompt_setting import get_prompts
from app.config.setting import settings
from app.core.logger import logger
from langchain_core.tools import tool
import re
import psycopg

from app.service.llm_service import get_openaillm
from app.core.utils import (dangerous_sql,forbidden_keywords)

SYSTEM_PROMPT = get_prompts.prompt["sql_agent_prompt"]
_ALLOWED_TABLES = set(t.lower() for t in settings.postgres["allowed_tables"])


def frame_query(question:str)->str:
        prompt = ChatPromptTemplate.from_messages([
                ("system" , SYSTEM_PROMPT),
                ("human", "{question}"),
        ])
        chain = prompt | get_openaillm().bind_tools([verify_sql_query])
        response = chain.invoke({"question" : question})
        
        if response.tool_calls:
             sql = response.tool_calls[0]["args"].get("sql","")
        elif response.content:
             sql = response.content
        else:
             sql = response.content

        return sql

def verify_sql(sql:str)->dict:
        
        """
        Validates SQL query for security issues such as dangerous keywords and disallowed table access.
        """

        if not sql:
            return { "valid" : False, "reason":"Empty Query"}
        
        sql_lower = sql.lower()

        msg = {}

        for kw in forbidden_keywords:
             if sql_lower in kw:
                msg = { "valid" : False, "reason" : "Forbidden Keywords" }
                logger.info(msg)
                return msg

        if ";" in sql.strip().rstrip(";"):
            msg = { "valid" : False, "reason" : "Multiple statements not allowed"}
            logger.info(msg)
            return msg
        
        for kw in dangerous_sql:
            if re.search(rf"\b{kw}\b" if kw.isalpha() else re.escape(kw),sql_lower):
                msg = { "valid" : False , "reason" : f"Forbidden Keyword:{kw}"}
                logger.info(msg)
                return msg
                
        
        referenced = set(re.findall(r"(?:from|join)\s+([a-zA-Z_][a-zA-Z0-9_]*)",sql_lower))
        disallowed = referenced - _ALLOWED_TABLES
        if disallowed:
            msg = { "valid" : False, "reason" : f"Identified Disallowed tables in query ->{disallowed}" }
            logger.info(msg)
            return msg

        msg = { "valid" : True , "reason" : f"Query is safe and refrence only allowed tables ->{referenced}"}
        logger.info(msg)
        return msg

verify_sql_query = tool(verify_sql)

def execute_query(query:str)->dict:
    dsn = settings.postgres_dsn()

    try:
        with psycopg.connect(dsn,connect_timeout=10) as conn:
               conn.read_only = True
               with conn.cursor() as cur:
                    cur.execute(query,("vijay@example.com",))
                    rows = cur.fetchall()
                    columns = [desc[0] for desc in cur.description] if cur.description else []
                    result_rows = [dict(zip(columns, row)) for row in rows]
        logger.info(f"SQL executed -> {len(rows)} rows returned")
        return {
            "success": True,
            "rows" :result_rows,
            "rows_count":len(rows),
            "error":None
        }  
    
    except Exception as e:
        logger.error(f"SQl execution failed ->{e}")
        return {
             "success": False,
             "rows" :[],
             "rows_count":0,
             "error":str(e)
        }
