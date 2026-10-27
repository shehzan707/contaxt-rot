# Initial R2 audit

Archive SHA256: `5403a8555b3e40953a2ed7e065d47954ffbbfb9e1d0cb79031dde30694b8fa50`. Existing source preserved. Initial execution: 24 tests, 23 passed, 1 missing rank-bm25 dependency (see part1_baseline_tests.txt).

Working CPU scaffolding: scoring, conditions, paired bootstrap, basic split checks, review gate and fixed prompts. Partial: real-data ingestion, tokenizer-dependent context placement, BM25 sentence mapping and compression cache. Defects: zero allocation quota, nested gold gate, resume skips failed rows, active three-model config, Hugging Face-only loader. GPU, long-context feasibility and genuine compression unverified. Model/tokenizer revisions unresolved. No scientific outputs exist.
