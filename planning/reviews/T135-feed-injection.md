# T135: Feed instruction isolation audit for the mock-only runtime

Three new acceptance tests use a hostile feed fixture containing instructions
to switch task/schema, invoke shell and write a sentinel. For all seven tasks,
the adapter receives only allowlisted source fields and the caller-selected
task. Shell/tool dispatch is forbidden in the test. Tool-shaped model responses
are rejected against every analysis schema, and the sentinel is never created.
The private audit contains no hostile source text. All three tests pass.

## Exact scope and remaining requirement

Structured payload fields named system, task, response_schema, tools and
output_path are stripped. The current adapter is deterministic and has no
instruction-following or tool-execution facility. Instruction-like prose INSIDE
an allowed text field is deliberately preserved as untrusted source data.
An extractive summary can therefore quote those words verbatim; output text is
not invariant when source text changes. The test verifies unchanged control flow
and schema, not identical summary strings for different source texts.

The board instruction to remove embedded instructions is not implemented as a
general prose sanitizer. Such a sanitizer cannot reliably distinguish a quoted
newsworthy instruction from an attack. Do not treat this mock-only audit as a
complete defense for a future LLM adapter, and do not silently mark that broader
requirement satisfied. A future adapter needs a separately enforced instruction/
data boundary, suitable adversarial tests and an explicit review of this gap.

No implementation was changed by this audit. Review is requested for the current
mock-only scope and this clearly recorded remaining requirement. No independent
review or version release is claimed.
