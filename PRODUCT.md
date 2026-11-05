# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Three confirmed audiences (2026-11-05, k_sze):

1. **k_sze himself** — self-directed learning of history/geography.
2. **Public online-learner demo** — shareable static link; anyone with the URL can explore the lessons.
3. **Job-search proof asset** — shown to interviewers as evidence of front-end craft (D3 SVG mapping, i18n, performance work); must hold up under scrutiny.

Implication: content must be factually defensible (cited sources in lesson data), the UI must impress technically literate reviewers, and everything must work from a bare static host.

## Product Purpose

An interactive history-and-geography learning app: explore clickable world maps (D3 SVG, four projections + 3D globe), study narrated historical journeys (Xuanzang's 629–645 pilgrimage, Magellan–Elcano circumnavigation) with rich multi-locale narratives, and quiz yourself (locate-the-country, name-the-country, journey-specific guess-the-route and guess-the-event modes). Success = a learner can move from seeing a country to knowing its facts and a historical route's story, in their own language.

## Positioning

Deep historical-journey storytelling on top of a precision-rendered SVG world map — full-fidelity 10m Natural Earth geometry with progressive rendering, historically researched stop-by-stop itineraries (per the *Record of the Western Regions* and voyage logs), and five full locales — which generic map-quiz sites do not offer.

## Operating Context

- Pure static SPA: any static file host; **must work over both `http://` and `file://`** (JSON is source of truth; `.js` twins of data files for file:// loads).
- Live data enrichment (country facts) from Wikidata; lesson data is vendored.
- Development: AI-agent (Hermes) implements; k_sze reviews and merges PRs on GitHub (branch `main` protected; reviewer `ksze`).
- Dev server must be host-reachable for the user's browser; the agent's container verifies headless (Playwright/Chromium) with pixel and DOM audits.

## Capabilities and Constraints

- Vanilla JS + D3, no framework, no build step; ES5-compatible patterns where file:// needs them.
- 5 locales: en-GB, fr-CA, zh-Hans, zh-HK, ja — all UI copy AND all lesson content (stop names, narratives, facts) localized.
- Four flat projections (equirectangular, Mercator, naturalEarth, robinson) + 3D globe; all 238 countries always visible; drag uses a low-res merged-path layer (quick layer) for performance.
- Journey lessons: step-through mode with animated route drawing, clickable stop dots with multi-visit popover, travel-order sidebar, no find/name quiz modes.
- Quiz design rules: distractor options use real neighbouring/historical entities, wrong time/place must not be implausibly far from correct answers.
- Historical accuracy bar: routes must stay on land where the traveler walked, no anachronistic infrastructure (no post-era bridges), coordinates from verified Wikidata QIDs (P625 + label cross-checks) or manual coords with provenance comments; dates only to attested precision; debated identifications flagged in the UI copy.
- Cache-busting via `?v=N` query params on every JS/CSS include — bump on content/behaviour changes.
- Open decisions: none recorded.

## Brand Commitments

- Name is fixed: **Xuanzang** (user decision, 2026-11-05). Internal `ATLAS_*` globals and `AtlasMap`/`AtlasFacts` module names are deliberately retained; do not rename them.
- Dark navy cartographic look is incumbent; treat code/assets as the authority until DESIGN.md exists (record it via `/impeccable document` if wanted).

## Evidence on Hand

- Two complete researched lessons: `lessons/xuanzang/journey.json` (46 stops, 629–645, sourced from *Record of the Western Regions* / Li Rongxi's *Biography* / Wriggins; reference route map wujiangfeng75/xuanzang-route-map) and `lessons/magellan/voyage.json` (Albo's log; precise anchorages).
- Live GitHub repo `kal-hermes/Xuanzang` with PR history and verification tooling (`tools/verify_*.py`, `tools/check_route_on_land.py`).
- No testimonials, press, or marketing assets exist; do not fabricate any.

## Product Principles

1. **Static-first, file://-proof** — every feature must survive a double-clicked index.html.
2. **History you can defend** — every stop, date, and route segment traceable to a source; disputed facts say so in the UI.
3. **Five locales, no second-class language** — new content ships in all five or it doesn't ship.
4. **Precision renders fast** — full 10m geometry, but interaction (drag, rotate) must never drop the map.
5. **Craft as portfolio evidence** — the code and the UI are both on display to expert reviewers.

## Accessibility & Inclusion

Confirmed requirement (2026-11-05): **reach basic WCAG AA** — contrast, visible focus indicators, and full keyboard operability (currently only partial keyboard support; this is a known gap to close, not a decision to make).
