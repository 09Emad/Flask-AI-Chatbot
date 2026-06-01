# Vector Search for RAG

## Why vectors matter

Vector representations let semantically similar text live closer together in a search space, which improves retrieval beyond exact keyword matches.

## Common Vector Store Choices

- FAISS for local or embedded demos.
- Chroma for developer-friendly local persistence.
- Pinecone or Weaviate for hosted production search.

## Minimal RAG Upgrade Path

1. Start with keyword-based retrieval.
2. Add embeddings.
3. Store embeddings in a vector database.
4. Add reranking for higher precision.
5. Evaluate retrieval and generation separately.

