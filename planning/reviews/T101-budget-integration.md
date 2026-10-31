# T101: Budget integration audit

The owner-authorized local implementation was integrated in f658a17. Its obsolete
local-work hold was reconciled through task_client.py. This follow-up connects
the public ProviderRegistry to the same persistent usage.sqlite budget ledger
used by configured analyses. Both factories now use one budget configuration
helper. Registry mocks reserve configured units before actual attempts, and the
workflow summary reports reservations without request contents.

## Verification

- Four registry regressions cover quota persistence across restart with fallback,
  cache hits without new reservations, retry quota enforcement before execution,
  and a content-free workflow usage summary.
- 46 provider-related tests passed, including existing zero-budget, paid opt-in,
  concurrent reservation, monthly rollover and fallback tests.
- Full offline suite: 328 tests, with the sole failure caused by the obsolete
  assertion that the board must always contain a local-work hold. That assertion
  is corrected; coordination tests were rerun separately after the correction.
- Board schema validation and dedicated local-work transition tests are retained.

## Limits

The public registry still admits only zero-cost local mock adapters. No paid or
external adapter has been enabled. Its existing process-local rate-limit clock
is preserved; the persistent ledger governs monthly unit limits and costs.
Actions cache restoration is best-effort mock state reuse, not a reliable shared
billing store for future paid execution. An independent client must review the
implementation before task completion. No version release is confirmed here.
