from threading import Lock

from transformers import AutoConfig, AutoModelForCausalLM, AutoModelForSeq2SeqLM, AutoTokenizer


class ModelRegistry:
    def __init__(self, generation_max_length, generation_min_length):
        self.generation_max_length = generation_max_length
        self.generation_min_length = generation_min_length
        self._lock = Lock()
        self._cache = {}

    def _load_model_bundle(self, model_name):
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        config = AutoConfig.from_pretrained(model_name)

        if getattr(config, "is_encoder_decoder", False):
            model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            model_type = "seq2seq"
        else:
            model = AutoModelForCausalLM.from_pretrained(model_name)
            model_type = "causal"

        return {
            "name": model_name,
            "tokenizer": tokenizer,
            "model": model,
            "type": model_type,
        }

    def get(self, model_name):
        with self._lock:
            if model_name not in self._cache:
                self._cache[model_name] = self._load_model_bundle(model_name)
            return self._cache[model_name]

    def list_models(self, model_specs):
        return [
            {
                "id": spec["id"],
                "name": spec["name"],
                "family": spec["family"],
                "description": spec["description"],
                "is_default": spec.get("is_default", False),
            }
            for spec in model_specs
        ]


class LLMService:
    def __init__(self, registry):
        self.registry = registry

    def generate(self, model_name, prompt):
        bundle = self.registry.get(model_name)
        tokenizer = bundle["tokenizer"]
        model = bundle["model"]

        inputs = tokenizer(prompt, return_tensors="pt", truncation=True)
        generation_kwargs = {
            "max_length": self.registry.generation_max_length,
            "min_length": min(self.registry.generation_min_length, self.registry.generation_max_length),
        }

        if bundle["type"] == "seq2seq":
            generation_kwargs.update(
                {
                    "pad_token_id": tokenizer.eos_token_id or tokenizer.pad_token_id,
                    "no_repeat_ngram_size": 3,
                    "do_sample": True,
                    "temperature": 0.7,
                    "top_p": 0.9,
                }
            )
        else:
            generation_kwargs.update(
                {
                    "pad_token_id": tokenizer.eos_token_id or tokenizer.pad_token_id,
                    "do_sample": True,
                    "temperature": 0.7,
                    "top_p": 0.9,
                }
            )

        outputs = model.generate(**inputs, **generation_kwargs)

        if bundle["type"] == "causal":
            prompt_length = inputs["input_ids"].shape[-1]
            generated_tokens = outputs[0][prompt_length:]
            return tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()

        return tokenizer.decode(outputs[0], skip_special_tokens=True).strip()

