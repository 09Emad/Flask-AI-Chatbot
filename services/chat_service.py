class ChatService:
    def __init__(self, session_store, retriever, llm_service, system_prompt, max_history_turns):
        self.session_store = session_store
        self.retriever = retriever
        self.llm_service = llm_service
        self.system_prompt = system_prompt
        self.max_history_turns = max_history_turns

    def _build_context(self, session, retrieved_chunks):
        recent_messages = session["messages"][-self.max_history_turns * 2 :]
        lines = [self.system_prompt]

        if retrieved_chunks:
            lines.append("Knowledge Base Context:")
            for index, chunk in enumerate(retrieved_chunks, start=1):
                lines.append(f"[{index}] Source: {chunk['source']}")
                lines.append(f"[{index}] Title: {chunk['title']}")
                lines.append(f"[{index}] Content: {chunk['content']}")

        if recent_messages:
            lines.append("Conversation History:")
            for message in recent_messages:
                speaker = "User" if message["role"] == "user" else "Assistant"
                lines.append(f"{speaker}: {message['content']}")

        lines.append("Assistant:")
        return "\n".join(lines)

    def handle_prompt(self, session_id, prompt, model_name, max_prompt_length):
        if not prompt:
            return {"error": "prompt is required"}, 400
        if len(prompt) > max_prompt_length:
            return {"error": f"prompt must be at most {max_prompt_length} characters"}, 400

        session = self.session_store.get_or_create(session_id)
        self.session_store.store_message(session, "user", prompt)

        retrieved_chunks = self.retriever.retrieve(prompt)
        conversation_input = self._build_context(session, retrieved_chunks)
        response = self.llm_service.generate(model_name, conversation_input)

        if not response:
            response = "I could not generate a response."

        self.session_store.store_message(session, "assistant", response)

        return {
            "response": response,
            "session": self.session_store.summary(session),
            "sources": [
                {
                    "source": chunk["source"],
                    "title": chunk["title"],
                    "score": chunk["score"],
                }
                for chunk in retrieved_chunks
            ],
        }, 200

