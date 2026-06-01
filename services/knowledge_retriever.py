from collections import Counter
from pathlib import Path
import re


def tokenize(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def chunk_text(text, chunk_size, overlap):
    text = text.strip()
    if not text:
        return []

    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(0, end - overlap)
    return chunks


class KnowledgeRetriever:
    def __init__(self, base_dir, chunk_size=900, overlap=140, top_k=3):
        self.base_dir = Path(base_dir)
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.top_k = top_k
        self.documents = self._load_documents()

    def _load_documents(self):
        documents = []
        if not self.base_dir.exists():
            return documents

        for file_path in sorted(self.base_dir.rglob("*")):
            if file_path.is_file() and file_path.suffix.lower() in {".md", ".txt"}:
                text = file_path.read_text(encoding="utf-8")
                for index, chunk in enumerate(chunk_text(text, self.chunk_size, self.overlap)):
                    documents.append(
                        {
                            "id": f"{file_path.stem}-{index}",
                            "source": str(file_path.relative_to(self.base_dir.parent)).replace("\\", "/"),
                            "title": file_path.stem.replace("-", " ").replace("_", " ").title(),
                            "content": chunk,
                            "token_counts": Counter(tokenize(chunk)),
                        }
                    )
        return documents

    def _similarity_score(self, query_tokens, document_tokens):
        if not query_tokens or not document_tokens:
            return 0.0

        overlap = 0
        for token in query_tokens:
            if token in document_tokens:
                overlap += min(query_tokens.count(token), document_tokens.get(token, 0))
        doc_length = sum(document_tokens.values()) or 1
        return overlap / doc_length

    def retrieve(self, query, top_k=None):
        query_tokens = tokenize(query)
        candidates = []

        for document in self.documents:
            score = self._similarity_score(query_tokens, document["token_counts"])
            if score > 0:
                candidates.append(
                    {
                        "source": document["source"],
                        "title": document["title"],
                        "content": document["content"],
                        "score": round(score, 4),
                    }
                )

        candidates.sort(key=lambda item: item["score"], reverse=True)
        return candidates[: (top_k or self.top_k)]

    def source_names(self):
        return sorted({document["source"] for document in self.documents})

