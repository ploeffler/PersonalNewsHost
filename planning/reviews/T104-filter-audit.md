# T104: Payload filtering and private audit

The adapter boundary filters each request through its kind-specific scalar
allowlist. Six acceptance cases spy on the actual request delivered to generate,
not merely the returned mock response. Nested configuration, system instructions
and tool declarations outside the allowlist are discarded. Allowed nested data
is rejected by the existing runtime validation.

## Corrections

- Every Runtime now defaults to audit.jsonl beside its private cache, covering
  the public registry as well as the configured analysis path.
- Audit files are opened with mode 0600 and O_NOFOLLOW. Existing permissions are
  tightened through the open descriptor before writing. A symlink fails before
  adapter execution. Cache hits do not create extra outgoing-attempt records.
- GitHub token formats supplement existing API-key, Bearer and private-key
  detection. Known configured secrets remain rejected before execution.
- Provider and task labels must be bounded identifiers, preventing multiline or
  free-text task descriptions from becoming audit metadata.

Audit records contain only provider ID, kind, task ID, serialized allowed-payload
byte count and timestamp. They contain no payload, model response or secret.
The default location remains under private state, not public docs.

## Verification and limitations

Five dedicated tests cover all six adapter allowlists, exact audit fields/size,
permissions before first write and on existing files, cache-hit behavior, known
secret formats, metadata constraints and symlink refusal. All five pass; all 46
provider tests and all three T103 acceptance tests also pass. Full integration
results are recorded in the task submission.

No real remote adapter is enabled. Pattern scanning cannot identify arbitrary
unknown credentials or personal data in prose. Runtime callers must pass known
secret values when using configured credentials. POSIX file permissions and
O_NOFOLLOW target the supported Linux runtime. Parent state directories must be
controlled by the service operator. No independent review or version release is
claimed by this implementation report.
