# Phase 8 - UI Review

**Audited:** 2026-03-27
**Baseline:** 08-UI-SPEC.md (approved design contract)
**Screenshots:** captured (desktop 1440x900, tablet 768x1024, mobile 375x812)

---

## Pillar Scores

| Pillar | Score | Key Finding |
|--------|-------|-------------|
| 1. Copywriting | 3/4 | Good labels overall; empty state body text diverges from spec wording |
| 2. Visuals | 3/4 | Strong dark theme with clear hierarchy; summary bar placement below cards loses prominence |
| 3. Color | 2/4 | Major drift from spec: dark mode palette (#0f1119) replaces spec light mode (#f8fafc); accent colors shifted |
| 4. Typography | 3/4 | Inter font (not spec system-ui) works well; price size 26px vs spec 28px; label size 11px vs spec 13px |
| 5. Spacing | 3/4 | Consistent spacing internally; a few spec deviations (80px empty state vs 64px, badge padding 2px vs 4px) |
| 6. Experience Design | 3/4 | Loading overlay, activity badge, keyboard nav on airport search are excellent; no error boundary on fetch failures |

**Overall: 17/24**

---

## Top 3 Priority Fixes

1. **Summary bar is buried below the cards grid** - Users must scroll past all cards to see aggregate metrics (active count, cheapest price, next polling). This defeats the spec purpose of a "glanceable status bar." Move `#summary-bar` above `.cards-grid` in `index.html` and restore the dark background bar style from the spec (or adapt it to the current dark theme with a distinct surface color).

2. **Empty state CTA button uses blue (#3b82f6) instead of spec green (#22c55e)** - The "Criar primeiro grupo" button in `index.html:57` is styled `.btn-create` with `background: #3b82f6`. The spec explicitly calls for green (#22c55e) to signal a positive, welcoming action. Change to `background: #10b981` (matching the current green palette) or `#22c55e` per spec.

3. **Chart line color not updated to spec accent** - In `detail.html:40`, the chart `borderColor` is still `#3b82f6` and `backgroundColor` is `rgba(59, 130, 246, 0.08)`. The spec Detail Page Contract requires `#0ea5e9` and `rgba(14, 165, 233, 0.1)`. Update both values in the Chart.js configuration.

---

## Detailed Findings

### Pillar 1: Copywriting (3/4)

The copy is generally well-crafted and domain-appropriate. Key observations:

**Matches spec:**
- "Editar" link: `index.html:401` - matches spec
- "Desativar"/"Ativar" toggle: `index.html:403-404` - matches spec
- "Aguardando coleta": `index.html:397` - matches spec
- "Voltar" link on detail: `detail.html:12` - matches spec
- "Sem sinal" badge: `index.html:377` - matches spec

**Deviations:**
- Empty state heading is split into `<h2>` + `<p>` at `index.html:351-352`. The spec says "no separate heading, combined with body." Current: heading "Nenhum grupo cadastrado" + body "Comece monitorando sua primeira rota. Voce recebera alertas quando o preco estiver bom." vs spec body "Nenhum grupo cadastrado. Comece monitorando sua primeira rota!" The added sentence about alerts is off-spec but arguably useful.
- "Buscar agora" button in `base.html:179` and "+ Novo Grupo" in `base.html:183` are not in the spec copywriting contract but are reasonable additions.
- "Ver voos" button in `index.html:411` is a new element not in the spec but provides good utility.
- "Salvar Alteracoes" in `edit.html:157` and "Criar Grupo" in `create.html:154` are clear, domain-specific labels.
- Missing accents in "Historico de Precos" (`detail.html:25`) and "Duracao" (`detail.html:19`).

**Forms copy (create/edit):**
- Form hints are excellent: "Um apelido para identificar esta busca. Ex: Portugal Julho" is clear and helpful.
- "Nenhum aeroporto encontrado" no-results state in airport search is handled.

### Pillar 2: Visuals (3/4)

**Strengths:**
- Clear visual hierarchy: price is the largest element on each card (26px monospace bold), making scanning easy.
- Card hover effect with `translateY(-4px)` and glow shadow creates good interactivity.
- The `::before` gradient line on cards adds subtle polish.
- Activity badge (floating bell icon) is a nice UX addition not in spec.
- Loading overlay with progress bar and contextual messages is polished.
- Sticky header with backdrop blur is professional.
- Inactive cards at `opacity: 0.4` clearly communicate disabled state.

**Issues:**
- Summary bar (`index.html:419-432`) renders as a plain inline text row below all cards. The spec calls for it to be a prominently styled bar at the TOP with dark background, 24px 32px padding, and border-radius 8px. Current implementation has `padding: 0`, `margin-top: 32px`, and appears as an afterthought visually. This is the most significant visual deviation from the spec.
- The card grid uses `minmax(380px, 1fr)` at `index.html:76` vs spec `minmax(340px, 1fr)`. This means cards break to single-column sooner on narrower desktop screens.
- No airplane icon visible on empty state SVG stroke differs: current uses `stroke="#3b82f6"` (blue) at `index.html:348` vs spec `stroke: #94a3b8` (muted gray).
- Card border radius is 12px (`index.html:84`) vs spec 8px.

### Pillar 3: Color (2/4)

The implementation has undergone a complete color paradigm shift from the spec's light mode to a dark mode theme. While the dark mode is visually cohesive and arguably more appropriate for a flight monitoring tool, it deviates significantly from the approved contract.

**Major deviations from spec:**

| Element | Spec | Actual | File:Line |
|---------|------|--------|-----------|
| Page background (dominant 60%) | #f8fafc (light) | #0f1119 (dark) | base.html:14 |
| Card background (secondary 30%) | #ffffff | #1a1e2e | index.html:82 |
| Body text color | (implied dark) | #f1f5f9 (light text) | base.html:15 |
| Header/Nav background | #1e293b | rgba(15,17,25,0.85) | base.html:22 |
| Summary bar background | #1e293b (dark) | none (transparent) | index.html:8-13 |
| LOW/Success border | #22c55e | #10b981 | index.html:106 |
| LOW price text | #22c55e | #34d399 | index.html:148 |
| MEDIUM border | #f59e0b | #f59e0b | index.html:107 (matches) |
| MEDIUM price text | #f59e0b | #fbbf24 | index.html:149 |
| HIGH border | #ef4444 | #ef4444 | index.html:108 (matches) |
| HIGH price text | #ef4444 | #f87171 | index.html:150 |
| Primary accent | #0ea5e9 | #3b82f6 | base.html:51 |
| Empty state CTA | #22c55e (green) | #3b82f6 (blue) | index.html:57 |
| "Voltar" link color | #0ea5e9 | #60a5fa | detail.html:12 |
| Chart line | #0ea5e9 | #3b82f6 | detail.html:40 |
| Card footer separator | #e2e8f0 | #2d3748 | index.html:167 |

**Consistent within dark theme:**
- The dark palette is internally consistent. Card backgrounds, borders, and hover states all work together.
- The green/yellow/red price coding is readable against the dark background (lighter variants #34d399, #fbbf24, #f87171 are appropriate choices for dark mode).
- No hardcoded colors outside the established palette.

**Verdict:** The dark mode is well-executed but the spec was approved with a light theme. Either the spec should be updated to reflect the dark mode decision, or the implementation should be brought back to spec. Scoring as 2/4 because the contract was not followed, even though the result is visually competent.

### Pillar 4: Typography (3/4)

**Font family:**
- Spec: `system-ui, -apple-system, sans-serif`
- Actual: `'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif` (base.html:13, loaded from Google Fonts at base.html:7-9)
- Inter is a deliberate upgrade. It falls back to system-ui. Acceptable deviation.

**Size audit:**

| Role | Spec | Actual | File:Line |
|------|------|--------|-----------|
| Body | 14px | 14px | Multiple (matches) |
| Label | 13px (0.8rem) | 13px for dates, 13px for footer | index.html:159, 170 |
| Heading (h1) | 20px | 20px | detail.html:14, create.html:61 (matches) |
| Price Display | 28px (1.75rem) | 26px | index.html:143 |
| Summary values | 20px bold | 13px semibold | index.html:27-28 |
| Summary labels | 13px, 400 | 13px, 400 | index.html:20-22 (matches) |
| Badge text | 13px, 700 | 11px, 700 | index.html:131-133 |
| Card name | (not specified) | 15px, 700 | index.html:121 |
| Form hints | (not in spec) | 12px | create.html:11 |

**Issues:**
- Price at 26px vs spec 28px: 2px smaller reduces the focal impact slightly.
- Summary values at 13px vs spec 20px: significantly smaller, reducing dashboard-at-a-glance utility.
- Badge text at 11px vs spec 13px: slightly small but still readable.

**Weight distribution:**
- 400 (normal): labels, body text
- 500 (medium): footer buttons, loading text
- 600 (semibold): summary values, form labels, buttons
- 700 (bold): headings, prices, badges, card names

Four weights in use (400, 500, 600, 700). Spec implied only 400 and 700. The extra weights (500, 600) add nuance without cluttering.

### Pillar 5: Spacing (3/4)

**Card padding:** 24px (1.5rem) at `index.html:85` - matches spec.
**Card grid gap:** 24px at `index.html:77` - matches spec.
**Card border-left:** 4px at `index.html:85` - matches spec.

**Deviations:**

| Element | Spec | Actual | File:Line |
|---------|------|--------|-----------|
| Empty state padding | 64px 32px | 80px 32px | index.html:32 |
| Summary bar padding | 24px 32px | 0 | index.html:12 |
| Summary bar margin-bottom | 24px | margin-top: 32px (below cards) | index.html:11 |
| Badge padding | (implied ~4px 8px) | 2px 8px | index.html:129 |
| Card border-radius | 8px | 12px | index.html:84 |
| Container padding | (not specified) | 32px | base.html:141 |
| Card footer separator spacing | (not specified) | padding-top: 16px | index.html:166 |

**Spacing consistency within the implementation:**
- 24px appears as a consistent "large" spacing unit (card padding, grid gap, margins).
- 16px as a "medium" unit (footer padding-top, form row gaps, mobile padding).
- 8px as a "small" unit (name-area gap, summary item gap).
- 4px for micro-spacing (card-route margin-bottom).
- The 4-multiple rule from the spec is followed throughout.

**Mobile responsiveness:**
- Container padding reduces to 16px on mobile (`base.html:162`).
- Cards go single-column (`index.html:337`).
- Summary bar gap reduces to 0 with items getting 16px horizontal padding (`index.html:335-336`).

### Pillar 6: Experience Design (3/4)

**Loading states:**
- Full loading overlay with progress bar, animated airplane icon, and contextual messages (`base.html:93-243`). This is significantly better than the spec minimum. The progress messages cycle through stages ("Iniciando busca...", "Buscando voos...", "Analisando precos...", "Detectando sinais...", "Finalizando...") which is excellent UX.

**Empty states:**
- Dashboard empty state with airplane SVG, descriptive text, and CTA button (`index.html:347-354`). Matches spec intent.
- Detail page no-data state: "Nenhum dado coletado ainda" (`detail.html:72`).
- Airport search no-results: "Nenhum aeroporto encontrado" (in JS).
- Awaiting data card state: "Aguardando coleta" (`index.html:397`).

**Error states:**
- Form validation errors displayed in create/edit forms (`create.html:64-67`, `edit.html:62-66`).
- `error.html` exists with centered layout and "Voltar ao inicio" CTA.
- Missing: no error handling for failed airport search fetch in `create.html:316-334`. If the `/api/airports/search` endpoint fails, the promise chain has no `.catch()`.

**Interaction patterns:**
- Card hover: transform + shadow transition.
- Keyboard navigation on airport autocomplete (ArrowUp/Down/Enter/Escape).
- Date mask with auto-slash insertion and flatpickr sync.
- Activity badge dropdown with click-outside-to-close.
- Touch device detection: `@media (hover: none)` disables hover transform on mobile (`index.html:339-341`).

**Accessibility concerns:**
- Activity badge uses `onclick` inline handler instead of button/role="button" with keyboard support.
- No `aria-label` on the activity badge bell icon.
- No `aria-label` on the "Ver voos" external link icon-button.
- The loading overlay has no `aria-live` region for screen readers.
- Airport search autocomplete lacks `role="listbox"` / `role="option"` ARIA attributes.

---

## Files Audited

- `app/templates/base.html` (245 lines) - base layout, header, loading overlay
- `app/templates/dashboard/index.html` (467 lines) - main dashboard with cards, summary, activity badge
- `app/templates/dashboard/detail.html` (75 lines) - group detail page with chart
- `app/templates/dashboard/create.html` (345 lines) - create group form with airport search
- `app/templates/dashboard/edit.html` (331 lines) - edit group form with airport search
- `app/templates/error.html` (11 lines) - error page

**Registry audit:** not applicable (no shadcn, no component registry)

**Screenshots captured to:** `.planning/ui-reviews/08-20260327-162849/`
- `desktop.png` (1440x900)
- `mobile.png` (375x812)
- `tablet.png` (768x1024)
- `create-desktop.png` (1440x900)
- `create-mobile.png` (375x812)
