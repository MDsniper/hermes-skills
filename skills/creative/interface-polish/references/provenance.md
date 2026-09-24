# Provenance and adaptations

Based on design principles from [Jakub Krehel's Make Interfaces Feel Better](https://github.com/jakubkrehel/make-interfaces-feel-better/tree/35545ea1512ad59fa463e6b1f95ca9c052981fe6), pinned at `35545ea1512ad59fa463e6b1f95ca9c052981fe6` (MIT). The upstream contains one skill, `make-interfaces-feel-better`, with five adjacent references: typography, surfaces, animations, icons, performance. This native skill packages its own concrete procedure and local checklist rather than copying a lone upstream entry point with broken sibling links.

Retained: existing-system fidelity; optical alignment, close nested-radius reasoning, structural borders, currentColor icons, restrained interruptible motion, explicit transition properties, meaningful static feedback, hit targets, scoped review and verification.

Changed deliberately:
- Accessibility/state contracts are first-class gates: keyboard focus, actual disabled behavior, live feedback, input retention and retries.
- Hardcoded scale/blur/spring prescriptions become context-sensitive starting points. No motion dependency is introduced and reduced motion wins.
- Font smoothing is optional, not universally “better”; preserve typeface and contrast.
- Tabular digits alone cannot reserve a new digit's space; add width/alignment when needed.
- GPU compositing/filter cost is measured, not guaranteed by a property name.
- Base-rule transitions work on hover exit too; icon-only buttons require names; state swaps must change the icon/semantics rather than animate the same glyph.

Upstream PR #5, “Four corrections to the guidance,” documents the last three concrete example problems (hover-exit transition, same-icon swap, missing button names, digit-count width). Its closed state alone is not evidence of merge; those issues remain observable in the pinned source. PR #1 clarified MIT, full-directory reference portability, optional commercial fonts, and target sizes. No upstream releases or automated test files were present in the inspected repository snapshot.

Verification limits: local fixtures exercise representative state, keyboard, reduced-motion and responsive paths. They do not cover every upstream animation pattern, font/browser, assistive technology or automatic skill triggering. Automated accessibility checks are scoped signals, not certification.

## Upstream MIT notice

MIT License

Copyright (c) 2026 Jakub Krehel

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
