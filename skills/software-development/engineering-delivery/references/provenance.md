# Provenance and scope

Original engineering synthesis for Hermes, informed by [Addy Osmani Agent Skills](https://github.com/addyosmani/agent-skills/tree/bcab6a1b8503100e8618c3b4e32cc78de43de769), pinned at `bcab6a1b8503100e8618c3b4e32cc78de43de769` (MIT).

Primary sources: `skills/spec-driven-development/SKILL.md`, `planning-and-task-breakdown`, `incremental-implementation`, `security-and-hardening`, `performance-optimization`, and `references/definition-of-done.md`. The upstream bundle has 25 distinct SKILL.md files, not 25 new installations here.

Adaptation: one concrete accepted-task/change/evidence procedure; locally packaged task/evidence templates; explicit native Hermes tools; no global install hooks, meta-router or automatic commit/deploy. Existing TDD, debugging, review and simplification skills remain authoritative specialists and are not overwritten. CI, migrations, observability and production-launch playbooks are not reproduced exhaustively.

Pitfalls verified from source and issue/release context:
- Release 0.6.10 removed automatic meta-skill injection; native discovery should not be wrapped in another router.
- Upstream #361 documents missing shared references on single-skill installs; local references are self-contained here.
- #599 reports a constraint guard blind to untracked files/deletions and reversed maximum-budget comparisons. Do not import that executable guard without independent tests.
- #602 reports soft “see skill” references not activating skills. This adaptation uses explicit `skill_view` steps while keeping its own substantive procedure.
- Structural/lexical upstream evals are distinct from token-spending behavioral evals. Representative local fixtures do not establish all 25 skills' behavior or automatic trigger reliability.

## Upstream MIT notice

MIT License

Copyright (c) 2025 Addy Osmani

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
