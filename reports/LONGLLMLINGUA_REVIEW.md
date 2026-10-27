# LongLLMLingua dependency review

Status: blocked, not validated. Original NousResearch/Llama-2-7b-hf and unresolved revision are preserved. No replacement selected or weights downloaded.

The public model card is readable without an account, but explicitly directs users to accept Meta's licence before requesting weights. Public visibility is not licence acceptance. The exact checkpoint's authorized anonymous weight access and an official identical Kaggle mirror have not been established. No Hugging Face registration is required by this project; unresolved legal access remains a gate.

The original adapter uses genuine upstream LongLLMLingua flags (condition_in_question, condition_compare, dynamic_context_compression_ratio and rank_method). A synthetic mocked contract test passes; this is not real compression. Static inspection of the published llmlingua 0.2.2 wheel confirms the required parameters exist (see compressor_api_inspection.json). Runtime API and actual long-input behavior require testing with installed dependencies and authorized weights. The compressed_prompt can include question text: record this and verify prompt equivalence before pilot. Reference-token budget mismatches deliberately fail.

Options requiring approval:
- Retain exact Llama-2-7B scorer after licence/access confirmation; process compression separately and unload it before Gemma. Approximate 14 GB decimal for 7B FP16 weights alone, plus activations/KV/cache and allocator overhead. No measured fit claim. Its native 4K context makes genuine 16K compression behavior a required check.
- Test a smaller causal scorer supported by PromptCompressor (upstream discusses GPT2-small). This changes the scoring model and must be a documented protocol amendment; long-input capability and output quality are not assumed. GPT2-small has roughly 0.25 GB FP16 weights before runtime overhead; actual compatibility untested.
- Upstream LLMLingua-2 BERT/XLM-R token classifiers are lighter alternatives, but constitute a different compression method. They cannot be relabeled LongLLMLingua. Resource expectations must be confirmed for the exact variant; no measured memory claim.

Sources inspected 2026-10-26:
- https://github.com/microsoft/LLMLingua (LongLLMLingua API and separate LLMLingua-2 example)
- https://huggingface.co/NousResearch/Llama-2-7b-hf (model architecture, 4K context and licence requirement)
