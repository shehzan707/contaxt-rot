# Technical audit

## Changes from R2
- Preserved original modules and tests, and archived the original configuration as protocol_r2.json.
- Activated only Gemma from version-pinned Kaggle; inactive Llama/Qwen references remain. Conditions and split sizes unchanged.
- Added architecture check, matching processor/tokenizer, local-only loading, streamed weight checksums and explicit BF16 capability rejection. No fabricated HF revision.
- Corrected EOS-at-output-cap status handling; empty responses receive malformed_answer.
- Fixed zero/negative allocation quotas and strengthened HotpotQA field validation.
- Added source download and transparent Parquet fallback conversion; quarantined one invalid supporting fact rather than repairing it without evidence.
- Added a reserved donor pool, provisional allocation manifest, explicit pending human-review queue and controlled construction CLI. Gold scoring file is separate. Evidence is inserted contiguously but remains sentence chunks, avoiding an oracle grouped-evidence advantage in BM25.
- Added source-id preservation for grouped chunks, recursive structured gold-field rejection, explicit split/condition/model selection, run limits, deterministic ordering, dry planning, expected manifests and append-only resume validation.
- Runner requires approved context-manifest hash and matches tokenizer configuration checksums against the loaded checkpoint. Native token counts are measured without truncation. All eight conditions remain available for test; held-out combinations are forbidden for development.
- Compression uses explicitly provided, identity/hash-checked local scorer files and local Kaggle reference tokenizer. Original scorer revision still must be resolved. No automatic HF model download or replacement.
- Added Colab setup/smoke notebook, diagnostic and synthetic feasibility scripts, setup guide, handoff and reproducibility reports.

## Actual validation
46 CPU tests passed. Tests are synthetic software fixtures, not research findings. They cover original scoring/statistics, conditions, split checks, BM25, grouped provenance, 4K/16K placement, prompt structure, recursive gold isolation, review gates, Kaggle version/precision gates, JSONL resume/corruption/duplicates, expected grids, compression call contract and simulated native overflow. Real dataset validation is separately documented in real_data_checks.json. Notebook schema and code syntax passed; real Colab execution failed before diagnostics could be measured.

LLMLingua 0.2.2 wheel was downloaded without weights and its compress_prompt signature inspected statically. Required arguments are present. This is NOT package import/runtime/compression validation. See compressor_api_inspection.json and LONGLLMLINGUA_REVIEW.md.

## Limitations requiring further engineering/verification
No real Gemma tokenizer/context output or generation was measured. No GPU memory/latency/precision conclusion is supported. Full environment compatibility and package locks remain unverified. Genuine LongLLMLingua long-input output semantics, memory use, retained evidence and question inclusion remain to be verified. Inference gate rejects structured annotation keys, but human review must still ensure prompt text itself has no annotation labels. No claim of mathematically impossible leakage is made.

Resume deliberately refuses prior failed rows and corrupt tails; recovery needs a separate explicitly named retry output. Concurrent processes writing the same file are not supported. Use one writer per output file. Detailed retry adjudication must precede statistical analysis.

No credentials, model weights or raw datasets are included in tracked files or the delivery archive. Existing historical R2 reports are labeled r2_* and are not current execution evidence.
