# LLM Evaluation

## What to measure

- Groundedness
- Faithfulness
- Context relevance
- Answer quality
- Latency
- Cost

## Practical evaluation methods

- Golden datasets for expected answers.
- Human review for nuanced quality checks.
- Automated retrieval metrics like recall@k.
- Prompt regression testing after changes.

## Production concerns

- Do not optimize only for fluency.
- Make the model show uncertainty when evidence is weak.
- Keep the evaluation harness close to the prompts you actually ship.

