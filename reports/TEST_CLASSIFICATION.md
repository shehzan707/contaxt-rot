# Test evidence

part1_baseline_tests.txt: 24 synthetic CPU tests executed initially; 23 passed and one missing dependency error.

part1_cpu_tests.txt: 46 synthetic CPU tests executed after repairs; all passed. No GPU required. Compression uses a mock, native overflow uses a fake tokenizer shape. Individual names and statuses are in the actual unittest output.

real_data_checks.json: actual 7,404 eligible HotpotQA records; schema, deterministic allocation and question/evidence separation passed. Dataset source had 7,405 records and one quarantined malformed evidence annotation. No synthetic questions substitute for benchmark data.

Notebook: nbformat validation and code-cell Python syntax passed; real end-to-end execution not passed.
