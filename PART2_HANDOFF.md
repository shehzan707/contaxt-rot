# Part 2 handoff — DO NOT RUN YET

Required gates: publication, licence consent, secure Kaggle authentication, real Gemma load, validated 4K/16K feasibility with approved precision, real LongLLMLingua compression, reviewed contexts, frozen manifests and actual package locks. These gates are not yet complete.

Pilot design: 2 reserved pilot questions × 2 conditions × 4 methods = 16 Gemma answer calls. Suggested technical pilot conditions C1 and C6 exercise both lengths and distractor types within development conditions. Confirm/freeze this choice before any calls; do not use pilot outcomes as final findings. No pilot has run.

After gates pass, precompute genuine LongLLMLingua compression for four pilot contexts in a separate process, log model load/compression overhead and cache hashes, then unload the scorer before Gemma. Review retained evidence separately without passing gold to the model.

Plan each method (no generation):
```sh
python -m src.run --contexts data/prepared/contexts.jsonl --approved-manifest data/prepared/approved_manifest.json --split pilot --conditions C1 C6 --method full --limit 4 --output results/pilot_full.jsonl
```
Repeat with bm25 and evidence and distinct output files. For longllmlingua, use the compressed JSONL and its generated .approved.json manifest. Compression requires --scorer-path, --reference-path, --scorer-manifest and --approved-manifest; the scorer manifest must identify the original model, pinned revision and file checksums. Verify each expected manifest has exactly four unique cells and all four methods total sixteen. Only after approval/readiness, add --execute to those four commands. Omit --limit for later full grids once their manifests are reviewed. Do not run additional models.

The runner loads only Gemma index 0 and blocks held-out conditions in development. Test uses all eight conditions. Failures are not research findings; retain raw outputs and status. Resume skips successful existing IDs, refuses malformed/duplicate logs and stops on failed prior IDs so retries cannot silently bias analysis. Commit/lock the final protocol, tokenizer/checkpoint and manifests before running.
