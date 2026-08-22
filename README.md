# StudentAgent

StudentAgent is a local, permission-aware CLI assistant for Canvas coursework and coding projects. The initial implementation provides normalized Canvas access, structured LLM tool calling, confirmation-aware tool execution, and an interactive CLI.

## Setup

Requires Python 3.12+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
cp .env.example .env
```

Set `CANVAS_BASE_URL`, `CANVAS_ACCESS_TOKEN`, and optionally `OPENAI_API_KEY` in `.env`. Never commit `.env`.

## Commands

```bash
sa --help
sa config
sa courses
sa assignments --days 7
sa chat
sa ask "what assignments are due this week?"
```

Without an OpenAI key, read-only Canvas commands still work when Canvas is configured; the chat command reports the missing LLM configuration clearly.

## Architecture

Integrations normalize provider responses into Pydantic models. Typed tools are registered with JSON schemas, validated before execution, capped by timeout/output limits, and gated by permission. The agent loop can execute multiple tool calls and converts failures into structured observations.
