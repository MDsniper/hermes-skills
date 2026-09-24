# Checks, Evidence, and Framework Mappings

The bundled helper is independently written, standard-library-only Python. It does not copy or run an upstream scanner. Its seven rules detect literal properties in sanitized **local** JSON; they are not effective-permission evaluation, runtime validation, an exploitability result, CIS certification or a compliance score.

## Supported Inputs and Evidence

- `--kind iam`: one IAM policy document, with nonempty `Statement` as a list or a single object. `Action` and `Resource` accept strings or nonempty lists. `NotAction`/`NotResource` are accepted but explicitly unassessed. This is not a full IAM schema validator. Trust relationships, SCPs, permission boundaries, resource policies, condition evaluation, and precedence of deny across statements/policies require separate manual analysis.
- `--kind compose`: one JSON object with a nonempty `services` object. This is a **subset** of Compose, not YAML, Docker inspect output or a Kubernetes manifest. Short and long volume declarations are considered. No interpolation, inheritance, merge, image resolution, profiles, includes or runtime state is resolved. Extra fields are ignored and covered by `unlisted_settings` in the report.
- Do not generate an export with live credentials on the user's behalf. Request a sanitized copy. No filesystem/daemon defaults are scanned. Any error makes the aggregate report `incomplete` and exit 2, even if other files contain findings.
- Findings include a source SHA-256 and structural `evidence.location`. `statement_index` indexes `Statement` after treating a singleton as a one-item list; `service_index` indexes the input JSON's `services` object in insertion order; `volume_index` indexes that service's `volumes` list. Field names are literal schema keys. These are **not JSON Pointers**. Resource/service names and source values are not copied into findings. A source relative filename is retained; avoid sensitive filenames.
- Exit 0 means **no candidates in the seven supported predicates**, not that omissions are resolved. Missing Compose user/privileged/read-only settings are listed as unknown, not inferred from defaults. All findings require human contextual review.

## Rules

| ID | Literal predicate | Default triage | Important exception or limitation |
|---|---|---|---|
| IAM001 | `Allow`, an Action containing `*` or `?`, and a literal `*` Resource (scalar or list) | High candidate | Conditions, SCPs, explicit deny and permission boundaries can constrain access. A named action with global resource is **not** flagged: some actions require it. Wildcard actions with ARN-scoped resources are outside this rule, not proven safe. |
| CMP001 | `privileged` is boolean true | High candidate | Specialist workloads may intentionally require it. Runtime namespace/isolation context is not available. String `"false"` is rejected, not interpreted by truthiness. |
| CMP002 | `network_mode` is exactly `host` | Medium candidate | Host networking may be justified; no connectivity test is performed. OS/runtime behavior can differ. |
| CMP003 | `cap_add` includes ALL or SYS_ADMIN (case-normalized; optional CAP_ prefix) | High candidate | This is not a complete capabilities audit. Other powerful capabilities and seccomp settings need manual review. |
| CMP004 | Short/long bind source is `/` or an absolute path ending `/docker.sock` | High candidate | A socket-like path may not be a management socket. Named volumes and `docker.sock.log` are not matched. Read-only socket mounts do not establish a read-only Docker API. Custom socket names and ancestor mounts are outside the predicate. |
| CMP005 | Explicit user is `root` or numeric UID zero, optionally followed by a group | Medium candidate | Missing user is unknown; the image can declare a non-root user. User namespaces/rootless runtimes may map container UID zero to an unprivileged host UID. Non-root user with group zero is not this predicate. |
| CMP006 | `read_only` is boolean false | Medium candidate | Writable root filesystems can be intentional. Missing `read_only` is unknown, and necessary writable directories may be supplied separately. |

Do not promote candidates to confirmed findings without the missing context. Suggested remediation must preserve workload function and include a rollback; the helper never writes changes.

## Transparent Mappings

Mappings below are **local analyst alignments**, not inherited automatically from upstream metadata, formal MITRE/NIST endorsements, or assertions that a tactic occurred. A workflow can support an outcome without satisfying it fully.

| Rules | NIST CSF 2.0 | ATT&CK risk context | D3FEND countermeasure concept | Rationale |
|---|---|---|---|---|
| IAM001 | PR.AA-05 | T1078.004 — Valid Accounts: Cloud Accounts | None asserted | Scope authorizations to reduce potential consequences of cloud account misuse. The configuration does not prove any compromised account. |
| CMP001, CMP003, CMP004 | PR.PS-01 | T1611 — Escape to Host | D3-EI — Execution Isolation | Review isolation-reducing configuration; an escape is neither attempted nor proved. |
| CMP002 | PR.IR-01 | None asserted | D3-EI — Execution Isolation (broad concept) | Review intentional namespace sharing and access boundaries, not an observed network attack. |
| CMP005 | PR.AA-05 | None asserted | None asserted | Review declared execution privilege and its runtime mapping. |
| CMP006 | PR.PS-01 | None asserted | None asserted | Review configuration management and intended writable state. |

NIST definitions: PR.AA-05 addresses managed/reviewed least-privilege authorizations; PR.PS-01 addresses established/applied configuration management; PR.IR-01 addresses protection from unauthorized logical access/usage. The static tool does not measure those organizational outcomes.

**ATLAS: not applicable to this helper.** It does not assess AI adversarial behavior. NIST AI RMF and MITRE F3 likewise have no asserted mapping here. Their upstream tags remain searchable catalog metadata, not validated findings.

## Primary Sources

Retrieved for this adaptation on 2026-09-24; retrieve current official documentation again when applying platform-specific remediation.

- [NIST CSF 2.0, CSWP 29, Appendix A](https://nvlpubs.nist.gov/nistpubs/CSWP/NIST.CSWP.29.pdf)
- [MITRE ATT&CK T1078.004](https://attack.mitre.org/techniques/T1078/004/)
- [MITRE ATT&CK T1611](https://attack.mitre.org/techniques/T1611/)
- [MITRE D3FEND Execution Isolation, D3-EI](https://d3fend.mitre.org/technique/d3f:ExecutionIsolation/)
- [AWS IAM Condition semantics](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_elements_condition.html)
- [Docker Engine security](https://docs.docker.com/engine/security/)
- [Cloudflare Access policy semantics](https://developers.cloudflare.com/cloudflare-one/access-controls/policies/) — manual review only; no Cloudflare API is called.

## Test Contract

Run through `terminal`: `python3 "<skill_dir>/scripts/test_audit.py"`.
Tests create and clean disposable files under `$TMPDIR` or `~/.hermes/cache/scratch`. No user configs are read. The helper child process is instrumented with Python audit hooks rejecting network/socket operations, child processes, shell execution, writes, mkdir, rename and remove. The test harness itself writes only synthetic fixtures and launches the reviewed helper; it is not a hostile-code sandbox.

Coverage includes positive/negative IAM and Compose cases, exact findings and hashes, non-echoing of synthetic sensitive values, scalar/list policy shapes, conditions and omissions, misleading text in unrelated fields, long/short mounts, missing configuration, string booleans, malformed JSON, duplicate keys, nonfinite constants, partial errors, file limits, symlinks, absolute/traversal paths, directories/FIFOs, duplicates and help. No cloud, Docker, Kubernetes, Terraform, network scanners or upstream scripts are exercised.
