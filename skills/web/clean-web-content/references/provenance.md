# Provenance and runtime

- Upstream: https://github.com/kepano/defuddle
- Tested release: 0.19.4, source commit `d4c4bad0dc96ca31b2383328e38061cc1490db47`.
- Published runtime: `defuddle@0.19.4`, npm integrity `sha512-Jz98aWlyEeuWcg9u2AavCEKknviI9GijMkrGFPk0wi1Lkfr1DDDw6XM+ak44Ol8kBDmDJsvU9Su2eUY09Fvh3Q==`.
- DOM runtime: `linkedom@0.18.12`. Every transitive npm version/integrity is recorded in the installed runtime's package-lock.json.
- Initially researched main commit `49d14ecc4089696565c2479b2f57db72be199adc`; its README, package.json and CLI/Node entry points are byte-identical to the chosen release in git diff. Do not confuse source-main research with the installed release pin.
- License: MIT, copyright (c) 2025 Steph Ango (@kepano). Full notice preserved in UPSTREAM-LICENSE.md.

The Hermes procedure, local-only wrapper and fixtures are first-party adaptations. Defuddle's actual extraction engine is retained, not claimed as a new parser. Reimplementing its site-specific extractors, metadata and document-cleaning logic would be impractical and less reliable. npm lifecycle scripts were disabled for installation; the resolved runtime lock contained no package with hasInstallScript set.

## Reproduction and updates

Use `terminal` to run the bundled offline tests. To reconstruct dependencies after an explicitly authorized reinstall, run `npm ci --ignore-scripts --no-audit --no-fund` in the existing isolated runtime directory; it consumes the retained lock. Do not replace it with a floating install or automatically upgrade on failure. Preserve runtime package.json and package-lock.json together.

No upstream SKILL.md exists in the researched Defuddle tree. Do not use the repository root as a Hermes skill shortcut. This Hermes-native skill is the integration artifact. Upstream request for a Hermes integration: https://github.com/kepano/defuddle/issues/349 (closed; not evidence that this adaptation is upstream-endorsed).

## Measured behavior (2026-09-24, macOS arm64)

- Published CLI reports 0.19.4 and parses the local article fixture as JSON.
- Wrapper preserves article beginning/middle/end, metadata, code, a data table, Unicode and relative-link destinations; removes the tested navigation/sidebar/footer/hidden content.
- Empty documents, obvious challenge titles, non-HTTPS or credential-bearing source URLs, and upstream internal diagnostics are rejected with nonzero exit and no success JSON.
- A live public GET of https://stephango.com/saw yielded the five-paragraph article; local extraction retained all article text, title and author. This is one measured page, not a site-wide benchmark.
- https://x.com/jack/status/20 returned public HTML with the post text. Defuddle emitted `Unknown pseudo-class :0` and fell back to noisy page content. The wrapper now rejects that degraded extraction. This is not proof X itself is universally inaccessible.

## Known limits

Extraction is heuristic and can remove meaningful material. Issue reports (not independently generalized): https://github.com/kepano/defuddle/issues/366 describes screen-reader fraction glyph loss; https://github.com/kepano/defuddle/issues/352 describes colon-ID selector fallback; https://github.com/kepano/defuddle/issues/348 reports a 403 difference from browser clipping. The colon-ID fallback is reproduced by the bundled fixture; other issue claims remain reports.

No full upstream test suite, browser renderer, authentication route, paywall access, security sandbox or HTML-sanitizer certification was exercised. `networkCalls:0` counts attempts through the disabled fetch hook during extraction; this is an application-level guard, not an OS network sandbox.
