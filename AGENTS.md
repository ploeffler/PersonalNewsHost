# Project development instructions

- Work only on `Full-featured-Newsoutlet`. Do not merge or push `main` without a new explicit human instruction. Do not force-push or discard another client's local work.
- Read `planning/project.json` for current product scope. No CMS and no per-avatar logins. Preserve the editorial departments, virtual employee identities, individual contributions and plugin-based shows.
- `planning/task-board.json` is authoritative for task status, dependencies, release assignment, leases and reviews. `planning/client-protocol.json` contains machine-readable command examples. Historical YAML files remain import references, not independent live status stores.
- Use a separate checkout per client. Before implementing a task, fetch the board and claim it using `scripts/task_client.py`, declaring explicit intended files or directory scopes. Begin only after the claim push is confirmed. Heartbeat while working and stop publishing when your lease expires or is replaced.
- Do not bypass `local_work_pending`: unfinished local 0.1 changes must first be deliberately reconciled and integrated by their owner/coordinator. The task client never transfers a client's uncommitted code.
- Commit tested implementation to the shared development branch with ordinary Git integration. Submit the committed SHA and check evidence. A different trusted client reviews and completes the task. Client IDs are self-declared coordination labels, not verified human identities.
- Run relevant tests. For task coordination: `python3 -m unittest discover -s tests -p test_task_client.py`. For release gating: `python3 -m unittest discover -s tests -p test_documentation_release.py`. Use the existing render tests for production changes.
- Task completion is not a version release. Complete all version tasks and integration checks before confirming the matching release marker and version tag.
- Consolidate visible documentation, generate diagrams and synchronize the wiki only after a confirmed completed/tested subversion. Do not publish wiki or regenerated graphics during ordinary task work.
- Explicit human requests to bootstrap or revise this coordination mechanism may be handled before the new board is published. Keep unrelated implementation edits intact and commit only the requested coordination changes.

- GitHub issues/milestones are a one-way view of the JSON board, synchronized by `scripts/sync_github_tasks.py`. Do not treat issue assignment or manual closure as task ownership/completion. `planning/github-task-map.json` stores IDs; keep human notes outside managed body blocks.
