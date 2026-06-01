# LLM + RAG Studio

A portfolio-grade Flask application with multi-model support, local retrieval, and a polished dashboard UI.

## What makes it stronger

- Multiple model families selectable from the UI.
- Retrieval from a local knowledge base before generation.
- Sources returned with each answer.
- Session-aware conversations with reset/export support.
- A more intentional UI that looks like a real AI workspace.

## Architecture

- `app.py` composes the application and exposes routes.
- `services/session_store.py` handles in-memory session state.
- `services/knowledge_retriever.py` handles document loading and retrieval.
- `services/llm_service.py` loads and runs different supported model families.
- `services/chat_service.py` orchestrates retrieval plus generation.

## Supported Models

- `facebook/blenderbot-400M-distill`
- `google/flan-t5-small`
- `microsoft/DialoGPT-medium`

## Knowledge Base

The local `knowledge_base/` folder contains material about:

- LLMs and RAG basics
- Vector search
- LLM evaluation
- Portfolio-ready AI engineering patterns

## Run

```bash
pip install -r requirements.txt
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

## Environment Variables

- `MODEL_NAME` - default model to load at startup
- `PORT` - Flask port, default `5000`
- `FLASK_DEBUG` - set to `1` for development mode
- `MAX_HISTORY_TURNS` - number of recent chat turns kept in context
- `MAX_PROMPT_LENGTH` - maximum accepted user prompt length
- `GENERATION_MAX_LENGTH` - generation length upper bound
- `GENERATION_MIN_LENGTH` - minimum generation length
- `RAG_TOP_K` - number of retrieved chunks passed to the prompt
- `RAG_CHUNK_SIZE` - chunk size for knowledge base documents
- `RAG_OVERLAP` - overlap used during chunking

## API

- `GET /health`
- `GET /models`
- `POST /session`
- `POST /chatbot`
- `POST /reset`
- `GET /export`
- `GET /templates`
- `GET /sources`

## Notes

- The first request may be slow because the selected model must be loaded.
- The retriever is local and lightweight; it is intentionally simple for a clean demo.
- You can swap the retriever for FAISS or another vector database later without changing the route layer.
