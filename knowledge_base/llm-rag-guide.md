<# LLM and RAG Guide

## What is an LLM?

An LLM is a large language model trained on large text corpora to predict and generate language. In products, it is usually paired with prompts, tools, or retrieval systems.

## What is RAG?

Retrieval-Augmented Generation combines a retriever and a generator. The retriever finds relevant context from a knowledge base, and the generator produces an answer grounded in that context.

## Typical RAG Pipeline

1. Split documents into chunks.
2. Convert chunks into searchable representations.
3. Retrieve top relevant chunks for a user query.
4. Feed retrieved context into the LLM prompt.
5. Generate an answer and optionally cite the sources.

## Good RAG Practices

- Keep chunks focused and not too large.
- Preserve source metadata such as file name and section title.
- Limit the number of chunks passed to the model.
- Ask the model to separate evidence from inference.
- Add evaluation for answer quality, retrieval quality, and hallucination rate.

## Common Failure Modes

- Retrieval returns the wrong document.
- Chunking destroys important context.
- The model answers from memory instead of evidence.
- The prompt is too long and drops the retrieved context.
- The system lacks source visibility for users.
