# Part 1 setup guide

This package is a verified partial setup, not pilot-ready. Start with reports/PART1_READINESS_REPORT.md. Original R2 source is retained; configs/protocol_r2.json preserves the old configuration.

## CPU setup
Use Python 3.11/3.12 in a virtual environment. From the project root:
```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python scripts/diagnostics.py
```
The local tested versions are in reports/environment_current.json. GPU/compressor requirement files are candidates, not proven compatibility locks.

## Data
```sh
python scripts/download_hotpot.py
python -m src.prepare data/hotpot_dev_distractor_v1.json data/prepared
```
If the original CMU host is unavailable, the audited fallback is public HotpotQA-namespace Parquet, requiring no login:
```sh
python -m pip install pyarrow==26.0.0
curl -L --fail https://huggingface.co/datasets/hotpotqa/hotpot_qa/resolve/main/distractor/validation-00000-of-00001.parquet -o data/hotpot_validation.parquet
python scripts/convert_hotpot_parquet.py
python -m src.prepare data/hotpot_dev_distractor_v1.json data/prepared
python -m src.build_contexts queue data/prepared --splits pilot
```
Original HTTP/HTTPS returned 503 in this session. Converted schema is equivalent in field structure, not original JSON bytes. Source/converted checksums and one quarantined invalid supporting-fact record are recorded. No index was guessed or repaired. Allocation remains provisional until context review.

## Human review and construction
Review each selected question's distractors for topical relevance, alternative answers, misleading relations, duplicates and source provenance. Set individual donor review_status to approved only after review. Set the group review_status, reviewer and review_notes. Do not approve automatically. The queue command refuses overwriting an existing review file. Reserve separate directories for later development/test queues, copying allocation and donor manifests from the same frozen preparation.
```sh
python -m src.build_contexts build data/prepared --tokenizer-path /path/to/pinned/kaggle/checkpoint
```
Construction uses the downloaded Gemma tokenizer for reference counts, whole gold evidence, 4096/16384 ±2%, midpoint .50/.90 ±.03. Chunks retain source_ids for grouped evidence. Gold is saved separately. Every context is hashed. Native formatted prompt counts are additionally measured during generation. Full real-context validation is blocked until tokenizer and approvals exist.

## Colab and Kaggle
Open notebooks/Part1_Gemma_Kaggle_Colab.ipynb in Colab and follow its cells. Free T4 was selectable, but actual runtime execution failed with Failed to fetch. No GPU specifications were measured. BF16 remains the R2 policy; the wrapper rejects unsupported hardware instead of silently switching precision. Gemma Request Access must be completed by the user. Create a Kaggle token yourself and save KAGGLE_API_TOKEN in Colab Secrets. Do not paste it in code or chat.

The exact intended handle is google/gemma-3/transformers/gemma-3-4b-it/1, verified on the official page. Checkpoint checksums are generated only after an actual download. None are invented. Use Gemma3ForConditionalGeneration and matching AutoProcessor with local_files_only=True.

## Publication
GitHub contents API returned 403 Resource not accessible by integration despite repo metadata showing push=true. Browser file upload requires the ChatGPT extension's Allow access to file URLs setting. No source was successfully published during this attempt. Once access is repaired, preserve any new remote content; use a dedicated branch/PR if main is populated. Never force-push. Commit only files allowed by .gitignore; raw data and review queues remain local.

## Results and safety
src.run defaults to planning only. --execute is a deliberate Part 2 action. No experiments run from setup. Preserve logs; malformed lines and duplicates halt resume. Failed runs require separate explicit retry output. Do not pool duplicate retries in analysis. All errors remain distinct from missing outputs and incorrect answers.
