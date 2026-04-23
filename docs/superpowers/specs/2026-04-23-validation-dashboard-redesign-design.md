# Validation Dashboard Redesign — Design Spec

**Date:** 2026-04-23
**Status:** Draft — awaiting user review
**Scope:** Frontend only. Data pipeline and JSON shape unchanged.

## 1. Problem

The validation dashboard at `validation-dashboard/dove-dashboard` shows whether AI digital-twin responses agree with real customer responses on the Dove body-wash study. Four pain points:

- **No hero / no answer.** Page opens with four equal-weight rows. Nothing tells a user at a glance whether twins matched customers.
- **Visual density.** Heavy neon palette, every pixel filled, monospace numbers everywhere — reads like a Bloomberg terminal.
- **Flat hierarchy.** Winners, Ranking, Heatmap, Insights sit at the same level. In reality some are "answer," some are "evidence," some are "deep dive."
- **Dual Real-vs-Twin clutter.** Two side-by-side `Tier1Card`s with an `AgreementBadge` between them force users to read in parallel.

The sibling `study-design-engine` Results dashboard (`study-design-engine/frontend/src/app/study/[studyId]/results/page.tsx`) solved the same class of problem: it opens with a hero recommendation, backs it up with a single evidence table, and parks deep-dive content below. This spec ports that pattern language to validation.

## 2. Scope

**In scope:** Redesign the **Aggregate** and **Individual** tabs.

**Out of scope for this pass:** Extended Aggregate, Extended Validation (retain current components; they'll inherit the pattern in a follow-up). Data pipeline changes. Backend integration. Moving to Next.js / the `study-design-engine` app.

## 3. Design principles

- **Verdict first.** Every tab opens with a hero card that answers "can I trust the twins on this" in one glance.
- **Narrow column.** `max-w-5xl` single column, not 1400px wide canvas. Forces hierarchy.
- **Restrained accent.** Darpan-lime (`#C8FF00`) used only for the answer / recommendation / active state. Green / amber / red reserved for agreement verdict semantics.
- **Same vocabulary as Results.** Card chrome, typography, spacing, motion, iconography all match `study-design-engine/frontend/src/components/results/*`. Users who've seen one can read the other.
- **Evidence pyramid.** Hero → summary table → diagnostic (collapsed) → deep insights (bottom).

## 4. Architecture

### 4.1 App location
Stays at `validation-dashboard/dove-dashboard`. Vite + React 19 + Tailwind 4. No framework change.

### 4.2 New dependencies
- `framer-motion` — for the `initial={{opacity:0, y:8}} animate={{opacity:1, y:0}}` fade-in pattern used by Results.
- `lucide-react` — icons (Trophy, TrendingUp, ArrowLeft, ChevronRight, Info, ChevronDown).

### 4.3 File changes
- `src/index.css` — rename design-token CSS vars to match Results: `--color-bg` → `--color-darpan-bg`, `--color-card` → `--color-darpan-surface`, `--color-border` → `--color-darpan-border`, etc. Hex values unchanged. Add `--color-darpan-lime`, `--color-darpan-lime-dim`, `--color-darpan-elevated`. Update `body` and scrollbar rules to reference new names. Update existing Tailwind class usages (`bg-card` → `bg-darpan-surface`, `border-border` → `border-darpan-border`, `text-primary` → `text-darpan-lime`, etc.) across all components.
- `src/components/layout/DashboardHeader.tsx` — restyled header (see §5.1).
- `src/components/aggregate/` — **new directory**, replaces `row1-winners/`, `row2-ranking/`, `row3-heatmap/`, `row4-insights/`. Contains the Aggregate tab components (see §6).
- `src/components/individual/` — refactored to use the hero-first shape (see §7).
- `src/App.tsx` — imports swap from `row*` dirs to `aggregate/`.
- Old `row1-winners/`, `row2-ranking/`, `row3-heatmap/`, `row4-insights/` directories deleted.

### 4.4 Fonts
Switch primary from Inter to **Space Grotesk** to match Results. Keep JetBrains Mono for tabular numbers. Google Fonts `<link>` in `index.html` updated; `index.css` `--font-sans` updated.

## 5. Visual language

### 5.1 Tokens (final names)

```
--color-darpan-bg         #0A0A0A
--color-darpan-surface    #111111
--color-darpan-elevated   #1A1A1A
--color-darpan-border     #2A2A2A
--color-darpan-border-active #333333
--color-darpan-lime       #C8FF00
--color-darpan-lime-dim   #9ACC00
--color-darpan-cyan       #00D4FF
--color-darpan-success    #00FF88   (Confirmed / Good)
--color-darpan-warning    #FFB800   (Directional / Acceptable)
--color-darpan-error      #FF4444   (Divergent / Poor)
```

Concept colors (`--color-concept-1..5`) unchanged.

### 5.2 Card chrome (standard)
```
bg-darpan-surface border border-darpan-border rounded-xl
```
Accent variant (for hero): left-border in verdict color, 3px, plus a faint outer glow at 5% opacity.

### 5.3 Motion
All top-level sections use `initial={{opacity:0, y:8}} animate={{opacity:1, y:0}}` with a 0.05s stagger per index, copied from Results. No pulse animations, no glow halos, no gradient shimmers.

### 5.4 Typography scale
- Hero headline: `text-xl font-bold text-white`
- Section title: `text-sm font-semibold text-white`
- Eyebrow: `text-xs font-medium text-white/30 uppercase tracking-wider`
- Body: `text-sm text-white/60 leading-relaxed`
- Tabular numbers: `font-mono tabular-nums`

## 6. Aggregate tab

### 6.1 Header (restyled `DashboardHeader.tsx`)

```
Studies  /  Dove Body Wash Concept Test  /  Validation

[Aggregate] [Individual] [Extended Aggregate] [Extended Validation]     n=17 real · n=17 twin · 5 concepts
```

- Breadcrumb replaces the status-dot + study-name line.
- Tab row uses the Results-style segmented control (`bg-darpan-surface rounded-lg p-0.5 border border-darpan-border`, active = `bg-darpan-lime/10 text-darpan-lime`).
- `n=` pills move to a quieter right-aligned group.
- No pulsing dot. No neon glow.

### 6.2 Section order
1. Research-question card *(new)*
2. Data-source toggle *(relocated from header)*
3. Hero verdict card *(new)*
4. Concept-agreement table *(new — replaces `WinnersRow` + `CompositeRankingChart`)*
5. Recommendation card *(ported from Results `Recommendation.tsx`)*
6. Diagnostic details — collapsible, default **closed** *(contains unified Δ heatmap + ranking chart)*
7. Deep insights — 3-card grid *(TURF / Order bias / Qualitative, restyled)*

### 6.3 Research-question card
Small card, `px-5 py-4`. Eyebrow `RESEARCH QUESTION`. Body: the study question text. Hardcoded string for Dove until study metadata is wired in (keep it as a prop so that slot exists).

### 6.4 Data-source toggle
Segmented control with three options: `Real · Twin · Both`. Lives under the research question. Same store (`useDashboardStore.dataSource`) drives visibility/dimming inside the evidence sections.

### 6.5 Hero verdict card

```
┌─────────────────────────────────────────────────────┐
│ ● CONFIRMED                    agreement  87%       │
│                                rank ρ     0.92      │
│ Twins match customers on this study                 │
│                                                     │
│ Twins ranked Deep Nourish #1, same as customers.    │
│ Friedman p=0.003 (significant). 4 of 5 concepts     │
│ fall in the same statistical tier.                  │
└─────────────────────────────────────────────────────┘
```

- Status dot + `{LEVEL}` label. Colors: `Confirmed` → `darpan-success`, `Directional` → `darpan-warning`, `Divergent` → `darpan-error`.
- Card has a 3px left border in the status color and a `boxShadow: 0 0 20px {color}10` outer glow.
- Two metric chips on the right (agreement % and Spearman ρ). `agreement` comes from `data.agreement` (needs a new computed field — see §8). `ρ` computed client-side from `data.real.composites` and `data.twin.composites`.
- Headline sentence — one of three templates keyed off `agreement.level`:
  - Confirmed: `"Twins match customers on this study"`
  - Directional: `"Twins partly match — read with caution"`
  - Divergent: `"Twins do not match — further testing needed"`
- Supporting sentence — auto-composed from `data.agreement.real_top`, `data.agreement.twin_top`, `data.real.friedman.p_value`, `data.real.friedman.significant`, and count of shared-tier concepts. Templates:
  - Confirmed: `"Twins ranked {real_top} #1, same as customers. Friedman p={p} ({sig/not sig}). {n} of {total} concepts fall in the same statistical tier."`
  - Directional: `"Twins ranked {twin_top} #1; customers ranked {real_top} #1. Overall ordering agrees on {n}/{total} pairs."`
  - Divergent: `"Twins ranked {twin_top} #1; customers ranked {real_top} #1. {n}/{total} concepts fall in different statistical tiers."`

### 6.6 Concept-agreement table

Columns: Concept · Real · Twin · Δ (twin − real) · Agreement bucket. One row per concept, sorted by Real composite descending. Shape mirrors `study-design-engine/frontend/src/components/results/ScoreTable.tsx`.

- Concept cell: colored dot (`CONCEPT_COLORS[name]`) + name.
- Real / Twin cells: `{composite}.toFixed(1)%`, `font-mono tabular-nums`, cell bg tinted by T2B band (reuse `t2bBg` logic from Results engine).
- Δ cell: signed number to one decimal, color-coded by magnitude (`|Δ|<5` green, `5–10` amber, `>10` red).
- Agreement cell: bucket label (`strong` / `moderate` / `weak`) with matching dot.
- `dataSource` controls column dimming: `real` → Twin col 20% opacity, `twin` → Real col 20% opacity, `both` → full.
- Legend strip below the table: `Δ = twin − real  ·  strong |Δ|<5  ·  moderate 5–10  ·  weak >10`.

### 6.7 Recommendation card

Port `study-design-engine/frontend/src/components/results/Recommendation.tsx` directly. Adjustments:
- Header sub-text: `"Based on real customer data, corroborated by twins"`.
- Ranked list: Real composites. Each row shows concept name + composite + a small twin-agreement indicator (`● strong`/`● weak` dot).
- Body copy: reuse `RecommendationStrip.tsx`'s logic for best-1 and best-2 selection (`turf.best_2`).

### 6.8 Diagnostic details (collapsible)

Disclosure card, default **closed**. Chevron toggles open.

**When open:**
- **Unified Δ heatmap** — single heatmap, 5 concepts × 6 metrics (pi, uniqueness, relevance, believability, interest, brand_fit). Cells show `twin - real` in pp, color ramp green (|Δ|<5) → amber (5–10) → red (>10). Replaces the two parallel `DiagnosticHeatmap`s. Tooltip on hover shows both Real and Twin T2B values plus Δ and n. Column headers clickable to drive `drilldownMetric` for the ranking chart.
- **Composite ranking chart** — restyled `CompositeRankingChart.tsx`. Softer grid, lime accents replace current green, no glow.

### 6.9 Deep insights

3-card grid: TURF · Order bias · Qualitative themes. Keep existing `TurfCard`, `OrderBiasCard`, `QualitativeInsightsCard` components but restyle each:
- `bg-card` → `bg-darpan-surface`
- `border-border` → `border-darpan-border`
- Remove `boxShadow` glows.
- Body copy to `text-white/60`.
- Section eyebrow to `text-white/30`.

## 7. Individual tab

Same header, same narrow column. Section order:

### 7.1 Selector (restyled `ParticipantConceptSelector`)
Two chip rows. Participant: `P01 … P17` plus `All`. Concept: five concept names plus `All Concepts`. Active chip uses `bg-darpan-lime/10 text-darpan-lime border border-darpan-lime/20`. Inactive chips: `bg-white/[0.02] text-white/40 border border-darpan-border`.

### 7.2 Hero fidelity verdict card *(new)*

```
┌─────────────────────────────────────────────────────┐
│ ● GOOD FIDELITY                 MAE       0.82      │
│                                 ±1 acc    84.2%     │
│ Twin P04 matches participant P04 on Deep Nourish    │
│                                                     │
│ Within ±1 on 12 of 14 metrics. Largest deviation    │
│ on believability (twin rated 4, real rated 2).      │
└─────────────────────────────────────────────────────┘
```

- Status + label keyed off **worst tier** across `quality.mae`, `quality.accuracy`, `quality.exact`. `Good` → `darpan-success`, `Acceptable` → `darpan-warning`, `Poor` → `darpan-error`.
- Metric chips: MAE (2 decimals) and ±1 accuracy (%).
- Headline templates:
  - Good: `"Twin {pid} matches participant {pid} on {concept}"`
  - Acceptable: `"Twin {pid} partly matches participant {pid} on {concept}"`
  - Poor: `"Twin {pid} diverges from participant {pid} on {concept}"`
- Supporting sentence: largest single deviation from `per_metric` (sort by `|diff|` desc, take first). Format: `"Within ±1 on {n}/{total} metrics. Largest deviation on {metric} (twin {twin}, real {real})."`
- When `selectedConcept === -1` (All Concepts), headline reads `"Twin {pid} vs participant {pid} across all concepts"`.
- When `selectedParticipant === 'all'`, this hero is replaced by the aggregate-summary variant (see §7.6).

### 7.3 Accuracy breakdown (demoted)
`AccuracyCard` components — 3-col grid, reduced scale. Value becomes `text-lg`, label `text-xs`, quality dot inline. Target threshold line ("target <1") kept as secondary text.

### 7.4 Per-metric comparison
Two-col grid:
- **RadarChartOverlay** — recharts radar. Restyle: grid stroke `#2A2A2A`, real fill `rgba(200,255,0,0.15)` lime, twin fill `rgba(0,212,255,0.15)` cyan, matching line strokes.
- **DeviationBarChart** — horizontal bars, twin − real per metric. Bars colored by sign (positive = cyan, negative = lime, `|diff|>1` full opacity, else 40%).

Both cards use standard darpan chrome; same motion fade.

### 7.5 Validation matrix
Section title: `Across all participants`. 17 × 5 heatmap. Each cell colored by MAE tier (Good/Acceptable/Poor). Click a cell to set `selectedParticipant` + `selectedConcept` in the store (jumps selector above). Legend strip below: `Good MAE<1 · Acceptable 1-1.5 · Poor >1.5`.

### 7.6 Summary cards (bottom)
`AggregateSummaryCards` — 3-card row: overall MAE, overall ±1 accuracy, % pairs in Good tier. Flat at the bottom of the tab. When the participant selector is on `all`, these cards get slightly elevated visual weight (since they are effectively the hero in that state).

## 8. Computed fields

No backend/pipeline changes. Two client-side computations added:

### 8.1 Rank Spearman ρ
Spearman ρ between `data.real.composites` and `data.twin.composites` over the shared concept name set. Computed in a new `src/lib/verdict-utils.ts`. Displayed in the hero metric chip.

### 8.2 Overall agreement %
Mean across concepts of `max(0, 1 - |Δcomposite|/100) * 100`, rounded to whole %. Computed alongside ρ in `verdict-utils.ts`. Displayed in the hero metric chip.

(These are intentionally simple derivations. They can be swapped for rigorous statistics later without changing the UI contract.)

### 8.3 Shared-tier count
From `data.real.tiers` and `data.twin.tiers`: count of concepts where the two sources assign the same tier. Used in the Confirmed supporting-sentence template.

## 9. Component migration plan

| Existing | Action | New location |
|---|---|---|
| `row1-winners/WinnersRow.tsx` | delete | — |
| `row1-winners/Tier1Card.tsx` | delete | — |
| `row1-winners/AgreementBadge.tsx` | delete (semantics move into hero verdict card) | — |
| `row1-winners/RecommendationStrip.tsx` | delete (logic ported into new Recommendation) | — |
| `row2-ranking/RankingRow.tsx` | delete | — |
| `row2-ranking/CompositeRankingChart.tsx` | move + restyle | `aggregate/CompositeRankingChart.tsx` (inside Diagnostic disclosure) |
| `row3-heatmap/HeatmapRow.tsx` | delete | — |
| `row3-heatmap/DiagnosticHeatmap.tsx` | delete (replaced by unified Δ heatmap) | — |
| `row3-heatmap/HeatmapCell.tsx` | port + adapt | `aggregate/DiffHeatmapCell.tsx` (shows Δ instead of T2B) |
| `row3-heatmap/ConceptDetailPanel.tsx` | keep if referenced, restyle only | `aggregate/ConceptDetailPanel.tsx` |
| `row4-insights/InsightsRow.tsx` | delete | — |
| `row4-insights/TurfCard.tsx` | restyle only | `aggregate/TurfCard.tsx` |
| `row4-insights/OrderBiasCard.tsx` | restyle only | `aggregate/OrderBiasCard.tsx` |
| `row4-insights/QualitativeInsightsCard.tsx` | restyle only | `aggregate/QualitativeInsightsCard.tsx` |
| `layout/SectionRow.tsx` | keep, restyle (simpler chrome) | unchanged path |
| `layout/DashboardHeader.tsx` | rewrite | unchanged path |
| `individual/IndividualValidationTab.tsx` | rewrite around hero card | unchanged path |
| `individual/AccuracyCard.tsx` | restyle, shrink | unchanged path |
| `individual/RadarChartOverlay.tsx` | restyle | unchanged path |
| `individual/DeviationBarChart.tsx` | restyle | unchanged path |
| `individual/AggregateMatrix.tsx` | restyle, make cells clickable | unchanged path |
| `individual/AggregateSummaryCards.tsx` | restyle, shrink | unchanged path |
| `individual/ParticipantConceptSelector.tsx` | restyle (chip form) | unchanged path |
| `shared/DataSourceToggle.tsx` | restyle | unchanged path |
| `shared/ConceptPill.tsx` | restyle | unchanged path |
| `shared/MetricTooltip.tsx` | restyle | unchanged path |

**New files:**
- `src/components/aggregate/AggregateTab.tsx` — top-level container
- `src/components/aggregate/HeroVerdictCard.tsx`
- `src/components/aggregate/ResearchQuestionCard.tsx`
- `src/components/aggregate/ConceptAgreementTable.tsx`
- `src/components/aggregate/RecommendationCard.tsx`
- `src/components/aggregate/DiagnosticSection.tsx` (disclosure wrapper)
- `src/components/aggregate/UnifiedDiffHeatmap.tsx`
- `src/components/individual/HeroFidelityCard.tsx`
- `src/lib/verdict-utils.ts` (Spearman ρ, overall agreement %, shared-tier count, headline composers)

## 10. Success criteria

- Opening the Aggregate tab: a user can read the verdict within 1 second and identify the top concept within 5 seconds, without scrolling past one fold on a 1440×900 display.
- Opening the Individual tab at default selection: user sees the hero fidelity verdict for that pair immediately.
- Visual diff against the Results dashboard: card chrome, typography, icon set, motion, spacing cadence are indistinguishable.
- No regression on data displayed — every value visible in the current dashboard remains accessible (some behind the Diagnostic disclosure).
- Extended Aggregate and Extended Validation tabs still render with their current components. They visually break from the new pattern; that is expected and called out in a follow-up spec.

## 11. Follow-up (not in this plan)

- Redesign Extended Aggregate and Extended Validation to the new pattern.
- Wire the research-question string to study metadata instead of hardcoding Dove.
- Replace the simple "overall agreement %" with a rigorous derivation.
- Port to `study-design-engine/frontend` as a native Next.js validation tab.
