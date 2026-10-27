# Context-Rot Research — Part 1

**Evaluating Context-Rot Mitigation Under Unseen Context Conditions: Evidence Reliability and Cost**

Gemma 3 4B Instruct from official Kaggle is the sole active experimental model. Original R2 modules retained. This is a **partial infrastructure delivery**, not a completed or pilot-ready study. No scientific evaluation has run.

Start: [Setup guide](PART1_SETUP_GUIDE.md), [Readiness report](reports/PART1_READINESS_REPORT.md), [Colab notebook](notebooks/Part1_Gemma_Kaggle_Colab.ipynb), [Part 2 handoff](PART2_HANDOFF.md).

Four methods: full context, rank-bm25 retrieval, genuine LongLLMLingua adapter (blocked), fixed evidence-focused prompt. Eight conditions and 2/12/40 split sizes preserved. Gold never enters deployment records; runtime gates and provenance checks fail closed.

Run CPU tests: `python -m unittest discover -s tests -v`. Data and model weights are not included. Source provenance and measured validation evidence are in reports. CPU unit tests use synthetic fixtures; real benchmark preparation is reported separately.
