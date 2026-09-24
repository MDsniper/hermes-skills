# Runtime setup and provenance

The renderer is self-contained under one tool directory. Nothing goes into the
Hermes venv or the global Python/npm environments.

## Tool directory layout

```
${HERMES_HOME:-$HOME/.hermes}/tools/markdown-pdf/
  venv/                      # Python 3.11+ virtualenv
  browsers/                  # playwright-managed chromium_headless_shell-1243
  fonts/
    NotoSansCJKsc-VF.ttf     # SHA-256 990c807e79c25662a5a9ecf7f971baeb2bf2eab9a559e5ecf15cdfdb8561d21f
    LICENSE.OFL              # SIL Open Font License 1.1 (Noto Sans CJK)
  requirements.in / requirements.lock   # identical copies live in this skill's references/
```

## Rebuild on a new machine

1. `uv venv <tools>/markdown-pdf/venv` (Python 3.11+), then
   `uv pip install --require-hashes -r references/requirements.lock` using the
   lock shipped with this skill. The lock pins markdown-it-py, Playwright,
   fontTools and pypdf; transitive pins carry hashes.
2. With that venv: `python -m playwright install chromium-headless-shell`
   (installs `chromium_headless_shell-1243` under `<tools>/markdown-pdf/browsers`;
   `render.py` sets `PLAYWRIGHT_BROWSERS_PATH` there and never launches a full
   browser profile).
3. Fonts: download **NotoSansCJKsc-VF.ttf** from the official
   `notofonts/noto-cjk` GitHub releases (Sans variable TTF), verify the SHA-256
   above (render.py refuses any other file), and place it with `LICENSE.OFL`
   under `<tools>/markdown-pdf/fonts/`.

## Provenance

First-party workflow inspired by daymade/claude-code-skills `daymade-docs/pdf-creator`;
no upstream code is copied. Backend is pinned Chromium via Playwright
(`backend: chromium-playwright` is recorded in each PDF's report), raw HTML is
never executed, images and file/network resources are rejected at parse time,
and every render is checked by `scripts/test_studio.py`.
