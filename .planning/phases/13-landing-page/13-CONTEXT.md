# Phase 13: Landing Page - Context

**Gathered:** 2026-03-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Criar pagina publica para visitantes nao logados na rota `/`. Quando logado, `/` continua mostrando o dashboard. Quando nao logado, mostra landing page com hero, secao "Como funciona", comparativo com diferenciais em 3 cards, e CTA para entrar com Google.

</domain>

<decisions>
## Implementation Decisions

### Estrutura e secoes
- **D-01:** Landing page tem 4 secoes: Hero (headline + subtitulo + CTA), Como funciona (3 passos), Comparativo (3 cards de diferenciais), CTA final
- **D-02:** Reutilizar o mesmo header de base.html (glassmorphism sticky). Ja tem logica logado/nao logado implementada na Phase 11.
- **D-03:** Rota `/` no dashboard_index condiciona: `if user` renderiza dashboard, `else` renderiza landing. Nao criar rota separada.

### Visual e tom
- **D-04:** Dark mode coeso com o dashboard. Mesmo fundo #0b0e14, accent sky blue #0ea5e9, Inter font. Experiencia visual continua entre landing e app.
- **D-05:** Tom casual e direto. Frases curtas, linguagem simples. Nada tecnico (sem mencionar booking classes ou revenue management). Ex: "Saiba quando comprar antes que o preco suba."

### Comparativo
- **D-06:** Secao "Por que somos diferentes" usa 3 cards com icone (SVG inline). Cada card explica um diferencial sem comparar diretamente com concorrentes. Ex: "Sinais antes do preco subir", "Monitoramento passivo 24h", "Alerta direto no seu email".

### Claude's Discretion
- Textos exatos do hero (headline, subtitulo)
- Textos dos 3 passos do "Como funciona"
- Textos e icones dos 3 cards de diferenciais
- Layout CSS (grid, spacing, breakpoints mobile)
- Icones SVG inline para os cards

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Codebase atual
- `app/routes/dashboard.py` — Rota GET "/" que precisa condicionar landing vs dashboard (linha 103)
- `app/auth/middleware.py` — "/" ja esta em PUBLIC_PATHS (nao precisa mudar)
- `app/templates/base.html` — Header com glassmorphism, condicional logado/nao logado ja implementado
- `app/templates/dashboard/index.html` — Template atual do dashboard (referencia de design)

### Design system
- Fundo: #0b0e14
- Texto: #e2e8f0
- Accent: #0ea5e9 (sky blue)
- Semantico: verde #22c55e, amarelo #f59e0b, vermelho #ef4444
- Font: Inter 400/500/600/700
- Escala: 13/14/20/28px

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `base.html`: header glassmorphism + condicional logado/nao logado (Phase 11)
- Botao "Entrar com Google" ja existe no header para nao logados
- Paleta CSS completa ja definida no base.html (Phase 9)
- Flash messages ja funcionam na rota `/` (Phase 11)

### Established Patterns
- Templates Jinja2 com heranca de base.html
- CSS inline em `<style>` dentro dos templates (nao ha arquivos CSS separados)
- SVG inline (ja usado no estado vazio do dashboard e no favicon)
- Dark mode: fundo escuro, texto claro, accent azul

### Integration Points
- `dashboard_index` em `/`: adicionar condicional `if user` → dashboard, `else` → landing
- Novo template: `app/templates/landing.html` (herda de base.html)
- Nenhuma mudanca necessaria no middleware ou auth

</code_context>

<specifics>
## Specific Ideas

- Hero com headline grande e CTA verde ("Entrar com Google" ou "Comecar gratis")
- Secao "Como funciona" com 3 passos numerados: 1) Configure seus voos 2) Receba sinais 3) Compre na hora certa
- 3 cards de diferenciais com icones SVG, nao tabela comparativa
- Mobile-first: stack vertical em mobile, grid em desktop
- CTA final repete o botao de login antes do footer

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 13-landing-page*
*Context gathered: 2026-03-29*
