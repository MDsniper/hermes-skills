# Contracts and evidence

The planner has no model calls and does not execute commands from JSON. It validates a DAG, rejects duplicate/missing ids and cyclic dependencies, and proposes a bounded batch. A running task reserves both its declared scopes and a concurrency slot. Read/read overlap is allowed; write/write and write/read overlap (including parent directories) serialize. Existing symlinks are resolved and scope escapes refused.

Statuses: `pending`, `running`, `verified`, `blocked`, `unknown`. Only pending tasks with all dependencies verified are eligible. Reconcile uncertain side effects before changing unknown to pending. The file has one parent writer; no concurrent state updates or automatic resumption is provided.

A verified task requires one passing receipt for every acceptance string:

```json
{"check":"exact acceptance text","command":"actual command run","exit_code":0,"log":"artifacts/check.log","sha256":"actual lowercase sha256 of the full log"}
```

Use `terminal` to collect actual test output and compute `shasum -a 256 artifacts/check.log`, then `patch` the contract. Never invent a log to make this validator green. The hash binds the stored bytes; it does not certify that the command ran or the behavior is correct. Parent review must reconcile the tool transcript, changed files and expected outputs.

The helper is not a filesystem sandbox or a process supervisor. Undeclared resources, later symlink changes, same-file aliases/case differences on unusual filesystems, and external service conflicts require human/parent reasoning or worktree/container isolation.
