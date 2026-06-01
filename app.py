import os
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

from services.chat_service import ChatService
from services.knowledge_retriever import KnowledgeRetriever
from services.llm_service import LLMService, ModelRegistry
from services.session_store import SessionStore


BASE_DIR = Path(__file__).resolve().parent
KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge_base"


def build_model_specs():
    return [
        {
            "id": "blenderbot",
            "name": "facebook/blenderbot-400M-distill",
            "family": "conversation",
            "description": "Fast conversational baseline for general chat.",
            "is_default": True,
        },
        {
            "id": "flan_t5",
            "name": "google/flan-t5-small",
            "family": "instruction",
            "description": "Instruction-tuned model that handles structured prompts well.",
        },
        {
            "id": "dialogpt",
            "name": "microsoft/DialoGPT-medium",
            "family": "conversation",
            "description": "Dialogue model with a more chatty style.",
        },
    ]


def default_model_name(model_specs):
    requested = os.getenv("MODEL_NAME")
    available_names = {spec["name"] for spec in model_specs}
    if requested and requested in available_names:
        return requested
    return next(spec["name"] for spec in model_specs if spec.get("is_default"))


def create_app():
    app = Flask(__name__)
    CORS(app)

    model_specs = build_model_specs()
    model_name = default_model_name(model_specs)

    session_store = SessionStore()
    retriever = KnowledgeRetriever(
        base_dir=KNOWLEDGE_BASE_DIR,
        chunk_size=int(os.getenv("RAG_CHUNK_SIZE", "900")),
        overlap=int(os.getenv("RAG_OVERLAP", "140")),
        top_k=int(os.getenv("RAG_TOP_K", "3")),
    )
    model_registry = ModelRegistry(
        generation_max_length=int(os.getenv("GENERATION_MAX_LENGTH", "180")),
        generation_min_length=int(os.getenv("GENERATION_MIN_LENGTH", "24")),
    )
    llm_service = LLMService(registry=model_registry)
    chat_service = ChatService(
        session_store=session_store,
        retriever=retriever,
        llm_service=llm_service,
        system_prompt=(
            "You are an AI engineering assistant specializing in LLMs and RAG. "
            "Use the provided evidence from the knowledge base when relevant. "
            "If the evidence is incomplete, say so clearly and separate facts from inference. "
            "Be practical, concise, and specific."
        ),
        max_history_turns=int(os.getenv("MAX_HISTORY_TURNS", "8")),
    )
    max_prompt_length = int(os.getenv("MAX_PROMPT_LENGTH", "700"))

    prompt_templates = [
        {
            "id": "rag_design",
            "label": "RAG Design",
            "prompt": "Design a production-ready RAG system for this use case and explain chunking, embedding, retrieval, reranking, and evaluation: ",
        },
        {
            "id": "llm_ops",
            "label": "LLM Ops",
            "prompt": "Help me design an LLM service with safety, monitoring, cost control, and latency constraints: ",
        },
        {
            "id": "rag_debug",
            "label": "RAG Debugging",
            "prompt": "My RAG pipeline is failing or returning weak answers. Help me debug the root cause and improve it: ",
        },
        {
            "id": "prompt_eval",
            "label": "Prompt Eval",
            "prompt": "Evaluate this prompt and suggest improvements for a more grounded RAG answer: ",
        },
    ]

    @app.route("/", methods=["GET"])
    def home():
        return render_template(
            "index.html",
            model_name=model_name,
            prompt_templates=prompt_templates,
            model_options=model_specs,
            knowledge_document_count=len(retriever.documents),
        )

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify(
            {
                "status": "ok",
                "model": model_name,
                "sessions": session_store.count(),
                "knowledge_documents": len(retriever.documents),
                "uptime_hint": "service ready",
            }
        )

    @app.route("/models", methods=["GET"])
    def models():
        return jsonify({"models": model_specs, "default_model": model_name})

    @app.route("/session", methods=["POST"])
    def create_or_return_session():
        data = request.get_json(silent=True) or {}
        session = session_store.get_or_create(data.get("session_id"))
        return jsonify({"session": session_store.summary(session)})

    @app.route("/chatbot", methods=["POST"])
    def handle_prompt():
        data = request.get_json(silent=True) or {}
        requested_model = data.get("model_name") or model_name
        if requested_model not in {spec["name"] for spec in model_specs}:
            return jsonify({"error": "unsupported model"}), 400

        payload, status_code = chat_service.handle_prompt(
            session_id=data.get("session_id"),
            prompt=data.get("prompt", "").strip(),
            model_name=requested_model,
            max_prompt_length=max_prompt_length,
        )
        payload["model"] = requested_model
        return jsonify(payload), status_code

    @app.route("/reset", methods=["POST"])
    def reset_conversation():
        data = request.get_json(silent=True) or {}
        session = session_store.reset(data.get("session_id"))
        return jsonify(
            {
                "status": "conversation reset",
                "session": session_store.summary(session),
            }
        )

    @app.route("/export", methods=["GET"])
    def export_conversation():
        session = session_store.get_or_create(request.args.get("session_id"))
        return jsonify(
            {
                "session": session_store.summary(session),
                "messages": session["messages"],
            }
        )

    @app.route("/templates", methods=["GET"])
    def get_templates():
        return jsonify({"templates": prompt_templates})

    @app.route("/sources", methods=["GET"])
    def get_sources():
        return jsonify(
            {
                "knowledge_documents": len(retriever.documents),
                "sources": retriever.source_names(),
            }
        )

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        debug=os.getenv("FLASK_DEBUG", "0") == "1",
    )
