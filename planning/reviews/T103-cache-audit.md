# T103: Cache and idempotency acceptance audit

The integrated runtime hashes canonical JSON containing namespace, provider ID,
provider revision, kind, task, model, prompt version, filtered payload and output
schema. Canonicalization sorts JSON keys; field order and discarded configuration
fields do not cause new calls. Text is preserved verbatim: whitespace and Unicode
spelling are not collapsed because they may affect provider output.

SQLite BEGIN IMMEDIATE serializes misses across independent processes. Successful
validated results survive restart; invalid responses are not cached and corrupt
rows are recomputed. The production workflow restores/saves state/providers.
Cache state and the mock usage ledger remain private, outside published docs.

## Evidence

Three new acceptance tests pass: canonical field ordering/discarded fields;
provider/schema isolation; four independent concurrent Python processes followed
by a new process. The latter uses a metered local mock and confirms one cache
miss and exactly one 0.01 reservation in SQLite across all five executions.
Existing runtime and budget tests cover model/prompt/task/revision invalidation,
namespace isolation, corrupt cache, retries and repeat configured feed analyses.
No real paid provider or network request is made.

## Limits

Actions cache restoration is best effort. An evicted cache can cause a new call;
it cannot guarantee billing idempotency across arbitrary distributed jobs. Local
SQLite provides serialization for processes sharing the same cache filesystem.
This version enables local mocks only. Shared reliable persistence is required
before future paid adapters are admitted. Independent review is still required;
this audit does not complete the task or release a version.
