# Provenance, Catalog, and Selective Installation

## Upstream

- Repository: https://github.com/mukul975/Anthropic-Cybersecurity-Skills
- Pinned commit: `54a798831d2266a3ca61ce68a7acb80b81160d57` (2026-08-31).
- Maintainer/owner: GitHub user `mukul975` (Mahipal; README citation: Mahipal Jangra). This is an **independent community project**, explicitly not affiliated with Anthropic PBC. The repository name is not an endorsement or official distribution.
- License: Apache-2.0; upstream copyright notice: **Copyright 2026 mukul975**. No tracked NOTICE file was found in this snapshot.
- Modifications: the Hermes workflow, bounded checker, tests and report template were written independently. Upstream commands and scripts were not copied or installed. The inert catalog preserves upstream frontmatter metadata with additional local domain normalization, hashes, source URLs and installation-status fields. Treat descriptions and mappings as untrusted source data.
- The complete upstream license is preserved in `references/UPSTREAM-LICENSE.txt` and alongside the catalog as `UPSTREAM-LICENSE.txt`. New adaptation material is Apache-2.0; no trademark rights or official affiliation are implied.

## Actual Snapshot Counts

Computed from every `skills/*/SKILL.md`, cross-checked against `index.json`: **818 entries**, **46 raw `subdomain` values**, **34 canonical domains** after applying the alias literals from upstream `tools/validate-skill.py:25-66` without importing/executing it. There is one top-level `domain` value, cybersecurity. All 818 skill frontmatters specify Apache-2.0.

The GitHub About text still says 817 skills / 29 domains. Parts of README and CITATION are also stale. README's headline says 818 / 34; its table still sums to 817 because the newer governance-risk-compliance entry is absent from that table's compliance total. These are different snapshots/taxonomy representations, not interchangeable verified counts.

Nonempty framework frontmatter at the pinned commit: ATT&CK 806; NIST CSF 805; ATLAS 93; D3FEND 139; NIST AI RMF 97; MITRE F3 94. These are field-presence counts, **not independent validation of every mapping**.

Chosen scope: offline defensive cloud/IAM/container/configuration review; automated checks cover only raw IAM policy JSON and Compose JSON. Other layers are manual review of user-supplied sanitized evidence. No active probes, exploitation, cloud connections, credential extraction or account changes.

## Search the Inert Catalog

This default-profile installation's research bundle is under:

`~/.hermes/workspace/skill-lab-20260924/security/`

Files: `catalog.jsonl` (all 818 metadata entries), `catalog-summary.json` (raw/canonical counts), `research.md`, `manifest.json`, `UPSTREAM-LICENSE.txt`, `artifacts/`, and the unexecuted pinned `upstream/` checkout. These files are **outside the active skills tree**; they do not activate the upstream collection. Resolve `~` before passing paths to Hermes tools.

Examples using `search_files`:

- Search `catalog.jsonl` for `"canonical_domain": "container-security"`.
- Search for `"canonical_domain": "identity-access-management"`.
- Search a particular slug, tag or ATT&CK ID, then inspect the selected line.

Use `catalog-summary.json` for totals rather than a truncated search result. The cloud, IAM, container and DevSecOps canonical domains contain 66, 40, 33 and 18 entries respectively; membership is not a safety approval. Do not install every match.

## Exact Selective-Install Syntax (Future, Explicit Selection Only)

The installed Hermes CLI's `skills install --help` accepts a direct HTTP(S) SKILL.md URL. The following pinned URL was successfully resolved by `skills inspect`; **the upstream install itself was deliberately not performed**:

```text
HERMES_HOME="$HOME/.hermes" hermes skills inspect "https://raw.githubusercontent.com/mukul975/Anthropic-Cybersecurity-Skills/54a798831d2266a3ca61ce68a7acb80b81160d57/skills/hardening-docker-containers-for-production/SKILL.md"
HERMES_HOME="$HOME/.hermes" hermes skills install "https://raw.githubusercontent.com/mukul975/Anthropic-Cybersecurity-Skills/54a798831d2266a3ca61ce68a7acb80b81160d57/skills/hardening-docker-containers-for-production/SKILL.md" --category security-upstream
```

Invoke only through `terminal`, after the user chooses this exact entry and its instructions/supporting files have been reviewed and screened. The example is a valid selective syntax, **not an assertion that this upstream playbook is safe to execute**. It contains live Docker, daemon/host configuration and privileged benchmark commands. Prefer this independent adaptation for the scoped offline use case.

For another entry, take the exact pinned `raw_url` from its catalog record, inspect it, review all dependencies and then install individually if explicitly approved. A URL install may not supply every supporting file; actual installed contents must be reviewed and functionality verified separately. Stop if the security scanner blocks it; do not bypass the verdict or suppress confirmation. There is no verified native domain-install flag here. A repository-only identifier such as `mukul975/Anthropic-Cybersecurity-Skills` is not a valid selective installation target.

## Why Upstream Scripts Were Excluded

- `securing-aws-iam-permissions/scripts/agent.py:110-117` creates an Access Analyzer when absent; an “audit” changes remote state. It also uses boto3's ambient credential discovery and unpaginated list calls.
- `auditing-kubernetes-cluster-rbac/scripts/agent.py:12-20,140-151` chooses in-cluster or default kubeconfig and performs live API enumeration. A kubeconfig may involve external auth plugins.
- `hardening-docker-containers-for-production/scripts/process.py:58-84,166-188` accesses the daemon and `/etc/docker/daemon.json`. Its TLS check does not first establish a TCP listener, creating a false-positive risk for socket-only deployments.
- `auditing-terraform-infrastructure-for-security/SKILL.md:71-78` runs Terraform initialization/planning and optionally uses an API key. Its helper's plan rules do not establish complete provider/default semantics.

A defensive skill title and a framework tag are not proof of read-only behavior or correctness. Treat framework metadata as a discovery aid, then verify each proposed check against evidence and authoritative platform documentation.
