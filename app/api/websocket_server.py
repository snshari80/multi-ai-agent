import json
from app.core.logger import logger
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage

from app.service.memory_service import get_memory


from app.graph.state import new_state
from app.graph.workflow import get_graph

app = FastAPI(
    title="Multi-Agent LangGraph AI",
    description="Orchestrator + Knowledge/SQL/Research/Author agents over WebSocket",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health():
    return { "status":"healthy", "message":"multi-agent-api"}

@app.websocket("/ws/agent")
async def agent_websocket(websocket:WebSocket):
    await websocket.accept()
    logger.info("Websocket client connected")

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({
                    "event":"error",
                    "message":"Invalid Json format"
                })
                continue

            session_id = payload.get("session_id","unknown")
            query = payload.get("query","")

            memory = get_memory(sessionid=session_id)

            history = memory.load_memory_variables({})["history"]

            if not query:
                await websocket.send_json({
                    "event":"error",
                    "message":"Empty Query"
                })
                continue

            logger.info(f"Received Session Id:{session_id} and Query:{query}")

            async def emit(event_type:str,agent:str,message:str,data:dict = None):
                msg = { "event" : event_type, "agent": agent, "Message" : message}
                if data is not None:
                    msg["data"] = data
                await websocket.send_json(msg)

            state = new_state(session_id=session_id,user_query=query,emit=emit)
            graph = get_graph()

            user_query = state.get("user_query")

            if "messages" not in state:
                state["messages"] = [HumanMessage(content=state["user_query"])]

            state["messages"] = history + state["messages"]

            state["messages"] = state.get("messages", []) + [
                HumanMessage(content=user_query)
            ]

            try:
                final_state = await graph.ainvoke(state)

                ai_response = final_state["final_response"]

                memory.save_context(
                    {"input": state["messages"][-1].content},
                    {"output": ai_response}
                )

            except Exception as e:
                logger.exception(f"{session_id} Graph execution failed ->{e}")
                await websocket.send_json({
                    "event":"error",
                    "message":f"Internal Server Error ->{e}"
                })
                continue

            await websocket.send_json({
                "event":"turn_complete",
                "trace_id":final_state.get("trace_id", ""),
                "agent" : "evaluator"
            })

    
    except WebSocketDisconnect as e:
        logger.info(f"WebSocket disconnected (code={e.code})")
    except Exception as e:
        logger.exception(f"Expection occured -> {e}")
        try:
            await websocket.close()
        except Exception:
            pass


if __name__=="__main__":
    import uvicorn
    uvicorn.run(app,host="0.0.0.0",port=8000)