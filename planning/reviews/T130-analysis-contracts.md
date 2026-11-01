# T130: Analysis output contract audit

Seven version-0.1 mock analysis tasks are defined in analysis_tasks.py: summary,
entities, classification, relevance, bias, duplicates and headline. Runtime
selects the task schema independently of payload fields, validates finite JSON
before caching, and applies the same schema to retries, fallback and cache hits.

Five new tests cover all seven schema-valid baselines; per-task invalid-response
retry followed by a cached valid response; per-task exhausted retries followed
by a separate valid fallback; missing/extra/nested fields, wrong types, bounds
and nonfinite numbers; and schema changes invalidating cached results. All pass.
The complete integration result is recorded in the task submission.

These are deterministic fixture/extractive baselines. Empty entity lists,
general classification and zero relevance are mock defaults, not substantive
analysis. Bias and duplicate baselines explicitly report assessed=false. No
claim of factual verification or production semantic analysis is made. No remote
model is enabled. Independent review and version release remain separate steps.
