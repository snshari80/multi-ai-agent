# Multi-Agent AI

A multi-agent AI application built with FastAPI, LangGraph, and WebSocket streaming for orchestrating collaborative AI workflows.

## Features

- WebSocket-based agent interaction endpoint
- Multi-agent orchestration flow
- Guardrails and PII masking support
- Search, knowledge retrieval, and authoring agents
- Docker-ready deployment

## Project Structure

- app/api/websocket_server.py - FastAPI websocket entrypoint
- app/agents/ - Agent implementations
- app/graph/ - Workflow and state orchestration
- app/service/ - LLM, search, and OpenSearch integrations
- app/config/ - Configuration and prompt settings

## Requirements

- Python 3.11+
- Docker (optional)

## Environment Setup

1. Copy the sample environment file:
   ```bash
   copy .env.example .env
   ```
2. Update the values in .env with your own keys and service endpoints.

## Local Development

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
uvicorn app.api.websocket_server:app --host 0.0.0.0 --port 8000
```

The app will be available at:
- http://localhost:8000/heath
- ws://localhost:8000/ws/agent

## Docker

Build the image:

```bash
docker build -t multi-agent-ai .
```

Run the container:

```bash
docker run -p 8000:8000 --env-file .env multi-agent-ai
```

## Security Notes

- Do not commit your .env file.
- Keep secrets in environment variables or a secure secret manager.
- Use .env.example as a safe reference template.

## License

This project is licensed under the MIT License.

