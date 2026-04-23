---
phase: 36
slug: multi-leg
status: draft
shadcn_initialized: false
preset: none
created: 2026-04-22
---

# Phase 36 — UI Design Contract: Multi-Leg Trip Builder

Contrato visual e de interacao para roteiros multi-trecho na Orbita. Consumido por planner, executor, ui-checker e ui-auditor. Deriva integralmente da paleta e tokens ja declarados em `app/templates/base.html` (rebrand Orbita). Todas as decisoes arquiteturais vem de `36-CONTEXT.md` (D-01..D-20).

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none (Jinja2 SSR puro, proibido framework JS conforme `CLAUDE.md`) |
| Preset | not applicable |
| Component library | none (HTML/CSS manual com tokens em `base.html`) |
| Icon library | SVG inline (stroke currentColor, stroke-width 1.75 ou 2, padrao herdado do header/base) |
| Font | Space Grotesk (body), JetBrains Mono (precos, codigos IATA, badges) |

Fonte canonica dos tokens: `app/templates/base.html` linhas 16-70. **Proibido hex hardcoded em templates novos** — sempre via `var(--token)`.

---

## Spacing Scale

Valores canonicos (grade 4px, ja declarados em base.html):

| Token | Value | Uso nesta fase |
|-------|-------|----------------|
| `--sp-1` | 4px | Gap entre icone e label dentro de botao `+ Adicionar trecho` |
| `--sp-2` | 8px | Gap entre campos inline (origin/destination), padding interno de badge `MULTI` |
| `--sp-3` | 12px | Padding vertical de input no construtor, gap entre breakdown rows no email |
| `--sp-4` | 16px | Padding interno de `<fieldset class="leg">`, gap entre campos empilhados |
| `--sp-5` | 20px | Margem entre blocos de leg na pagina de detalhe |
| `--sp-6` | 24px | Gap vertical entre trechos no construtor, padding do card multi |
| `--sp-8` | 32px | Separacao entre header do form e primeiro trecho |
| `--sp-12` | 48px | Margem inferior do container principal |

Excecoes: nenhuma. Construtor dinamico nao introduz espacamentos fora da escala.

---

## Typography

Escala ja fixada pelo rebrand Orbita (base.html body = 14px / Space Grotesk). Phase 36 reusa; nao adiciona tamanhos novos.

| Role | Size | Weight | Line Height | Uso nesta fase |
|------|------|--------|-------------|----------------|
| Caption/mono | 12px | 500 (mono) ou 700 | 1.4 | Badge `MULTI`, codigo IATA na cadeia, numero do trecho no legend |
| Body/label | 13px | 500 | 1.5 | Labels de campos do construtor, label `Preco total do roteiro`, legendas de breakdown |
| Body default | 14px | 400 | 1.5 | Copy corrida, mensagens de erro, disclaimer |
| Heading seccao | 16px | 600 | 1.3 | `Trecho N` legend do fieldset, titulo de secao no detalhe |
| Price display | 28px | 700 (mono) | 1.2 | Total do roteiro no card multi e no detalhe (mesma escala do card roundtrip, mantem paridade D-16) |

Weights permitidos: **400, 500, 600, 700** (ja em Space Grotesk). Pesos 500/700 ja em JetBrains Mono. Nenhum novo peso.

---

## Color (60/30/10)

Distribuicao ja estabelecida pelo rebrand. Phase 36 **nao introduz cor nova**, apenas reusa tokens:

| Role | Token | Value | Uso |
|------|-------|-------|-----|
| Dominant 60% | `--bg-0` | #070A13 | Fundo global da pagina, fundo do container |
| Dominant 60% | `--bg-1` | #0E1220 | Fundo de cards e fieldsets `.leg` |
| Secondary 30% | `--bg-2` | #161B2E | Separador entre trechos no construtor, fundo de breakdown row no detalhe |
| Secondary 30% | `--bg-3` | #1F2542 | Fundo de input focado/hovered, fundo de chip de cadeia no header do card |
| Accent 10% | `--brand-500` | #6366F1 | Toggle ativo (Multi-trecho), botao primario `+ Adicionar trecho`, foco de input |
| Accent 10% | `--accent-500` | #22D3EE | **Exclusivo do modo multi**: badge `MULTI`, seta ` -> ` na cadeia de trechos, borda de destaque do card multi |
| Semantica | `--success-500` / `--success-bg` | #10B981 / rgba | Recomendacao COMPRE AGORA (reuso Phase 34) |
| Semantica | `--warning-500` / `--warning-bg` | #F59E0B / rgba | Recomendacao AGUARDE (reuso Phase 34), aviso de quota SerpAPI baixa |
| Semantica | `--danger-500` / `--danger-bg` | #EF4444 / rgba | Erro de validacao temporal, botao `Remover trecho` em hover, acao destrutiva |
| Borders | `--border-2` | rgba(255,255,255,0.10) | Borda padrao de fieldset e input |
| Borders | `--border-3` | rgba(255,255,255,0.14) | Borda de input focado, borda do card multi ativo |

**Accent 10% (`--accent-500` ciano) reservado exclusivamente para:**
1. Badge `MULTI` no card do dashboard (fundo `rgba(34,211,238,0.12)`, texto `--accent-500`, fonte mono 12px 700)
2. Seta de cadeia ` -> ` entre codigos IATA no card, detalhe e email
3. Hover do toggle `Multi-trecho` quando inativo (preview)
4. Pontinho de transito do logo Orbita (ja existente, nao muda)

Nao usar ciano em botoes, badges de outros tipos ou em mais de 1 elemento por viewport alem dos listados.

Destructive `--danger-500` reservado a:
1. Mensagem de erro de validacao temporal ("Trecho 2 precisa sair em ou apos 20/06/2026")
2. Botao `Remover trecho` em hover (estado default e `--text-2` ghost; so acende vermelho no hover)
3. Aviso de quota SerpAPI zerada no topo do form

---

## Copywriting Contract

**Regras pt-BR invariantes (CLAUDE.md):** acentuacao correta, proibido travessao (usar ponto ou virgula), proibido emoji. Setas visuais usam ASCII ` -> ` (espaco-hifen-maior-espaco).

### Form de criacao (`/groups/create`)

| Elemento | Copy |
|----------|------|
| Toggle (rotulo) | `Tipo de roteiro` |
| Toggle opcao 1 (default) | `Roundtrip simples` |
| Toggle opcao 2 | `Multi-trecho` |
| Subtitulo modo multi | `De 2 a 5 trechos sequenciais. O sinal de compra considera o preco total do roteiro.` |
| Legend do fieldset | `Trecho N` (N = numero do trecho, comecando em 1) |
| Label origem | `Origem (IATA)` |
| Label destino | `Destino (IATA)` |
| Label janela inicio | `Saida a partir de` |
| Label janela fim | `Saida ate` |
| Label min stay | `Estadia minima (dias)` |
| Label max stay | `Estadia maxima (dias, opcional)` |
| Placeholder max stay | `Sem teto` |
| Botao adicionar | `+ Adicionar trecho` |
| Botao remover | `Remover trecho` |
| CTA primario | `Criar grupo multi-trecho` (quando modo = multi), `Criar grupo` (quando modo = roundtrip) |
| Hint auto-calculo | `Janela preenchida a partir do trecho anterior. Edite se precisar.` |

### Mensagens de erro (validacao temporal)

| Cenario | Copy |
|---------|------|
| leg[N+1] sai antes do minimo | `Trecho {N+1} precisa sair em ou apos {DD/MM/AAAA}. Ajuste a janela ou reduza a estadia minima do trecho {N}.` |
| Menos de 2 trechos | `Roteiro multi-trecho exige pelo menos 2 trechos. Use o modo Roundtrip simples para um unico trecho.` |
| Mais de 5 trechos | `Maximo de 5 trechos por roteiro. Divida em grupos menores se precisar monitorar mais.` |
| Min stay < 1 | `Estadia minima precisa ser de pelo menos 1 dia.` |
| Max stay < min stay | `Estadia maxima nao pode ser menor que a minima.` |
| IATA invalido | `Codigo IATA deve ter 3 letras (exemplo: GRU, FCO, MAD).` |

### Card do dashboard (multi) — D-16

| Elemento | Copy |
|----------|------|
| Badge | `MULTI` (mono, 12px, 700, fundo `rgba(34,211,238,0.12)`, cor `--accent-500`) |
| Cadeia | `GRU -> FCO -> MAD -> GRU` (mono, 14px, 500, seta em `--accent-500`, codigos em `--text-0`) |
| Label preco | `Preco total do roteiro` (13px, 500, `--text-2`) |
| Preco | `R$ X.XXX,XX` (mono, 28px, 700, `--text-0`) |
| Numero de trechos | `N trechos` (12px, 500, `--text-3`) |
| Recomendacao | reusa copy de Phase 34 (`Compre agora` / `Aguarde ate DD/MM` / `Monitorar`) |

### Pagina de detalhe (`/groups/{id}`) — D-18

| Elemento | Copy |
|----------|------|
| Titulo secao breakdown | `Combinacao mais barata encontrada` |
| Header da linha de leg | `Trecho N: ORIG -> DEST` |
| Label data do leg | `Saida em {DD/MM/AAAA}` |
| Label preco do leg | `R$ X.XXX,XX` (mono, 20px, 700) |
| Label companhia | `via {AIRLINE}` (13px, 500, `--text-2`) |
| Separador total | linha `--border-2`, margem `--sp-4` |
| Label total | `Total do roteiro` (14px, 600) |
| Valor total | `R$ X.XXX,XX` (mono, 28px, 700, `--text-0`) |
| Cluster comparadores | `Comparar este trecho em` (13px, 500, `--text-2`) seguido dos 4 botoes por leg (D-17) |

### Email consolidado multi — D-19, D-20

| Elemento | Copy |
|----------|------|
| Subject | `Orbita multi: {nome_grupo} R$ X.XXX,XX ({N} trechos)` |
| Header cadeia | `GRU -> FCO -> MAD -> GRU` (mono, 20px, 700 no HTML do email) |
| Label total no topo | `Preco total do roteiro` |
| Valor total | `R$ X.XXX,XX` (mono, 28px, 700, `--brand-500`) |
| Tabela breakdown header | `Trecho` · `Rota` · `Data` · `Preco` (13px, 600, `--text-1`) |
| Linha breakdown | `{N}` · `{ORIG -> DEST}` · `{DD/MM/AAAA}` · `R$ X,XX` |
| Rodape breakdown | `Total: R$ X.XXX,XX` |
| CTA plain text fallback | `Ver detalhes em https://orbita-flights.fly.dev/groups/{id}` |

### Estados transversais

| Elemento | Copy |
|----------|------|
| Empty state (grupo multi sem snapshot) | `Primeira busca em andamento. O preco total aparece apos o proximo ciclo de polling.` |
| Aviso quota SerpAPI baixa | `Quota SerpAPI do mes baixa. Rotas fora do cache podem ficar pendentes ate virada do mes.` |
| Confirmacao criacao | `Grupo multi-trecho criado. Primeira busca agendada.` |
| Confirmacao edicao | `Grupo atualizado.` |
| Confirmacao remocao | `Grupo removido.` |
| Confirmacao destrutiva | `Remover grupo` seguido de `Esta acao apaga o grupo e seus snapshots. Confirmar?` (modal ou inline confirm — planner decide, mas a copy e fixa) |

---

## Interaction Contract — Construtor Dinamico (D-08, D-09)

Interacao nova desta fase. Define contrato que o executor precisa cumprir em JS vanilla inline (`<script>` dentro de `create.html`/`edit.html`). Sem framework, sem bundler.

### Estados do toggle

| Estado | Visual |
|--------|--------|
| `Roundtrip simples` ativo (default) | Botao com `background: var(--brand-500)`, texto branco. Campos roundtrip visiveis, construtor `<section data-mode="multi">` com `display: none`. |
| `Multi-trecho` ativo | Mesmo tratamento visual no segundo botao. Campos roundtrip `display: none`, construtor visivel com 2 trechos pre-criados. |

Ambos os botoes inativos usam `.btn-ghost` (`border: 1px solid var(--border-2)`, `color: var(--text-1)`).

### Ciclo de vida do construtor

1. **Inicial (modo multi ativado):** renderiza 2 `<fieldset class="leg">` prontos. Leg 1 com janela vazia; leg 2 com janela preenchida via `recalcLegs()` apos usuario digitar em leg 1.
2. **Adicionar trecho:** botao `+ Adicionar trecho` visivel se `current_count < 5`. Clona `<template id="leg-template">`, atribui `data-order`, renumera legend (`Trecho N`), anexa, dispara `recalcLegs()`. Animacao: `opacity 0 -> 1` e `translateY(8px) -> 0` em 200ms ease-out (respeita `prefers-reduced-motion`).
3. **Remover trecho:** botao `Remover trecho` visivel apenas quando `current_count > 2`. No clique, remove elemento, renumera legends sequencialmente (`Trecho 1`, `Trecho 2`, ...), dispara `recalcLegs()`.
4. **Auto-calculo (D-09):** funcao `recalcLegs()` disparada em `input` nos campos `window_end` e `min_stay_days` de qualquer leg. Para cada `leg[N]` com N > 1 e sem `data-manual-override="true"`:
   - `window_start = leg[N-1].window_end + leg[N-1].min_stay_days`
   - `window_end = window_start + (leg[N-1].max_stay_days || 30)`
5. **Override manual:** quando usuario edita `window_start` ou `window_end` de um leg diretamente, marca `fieldset.dataset.manualOverride = "true"`. `recalcLegs()` preserva valores desses legs.

### Validacao client-side (UX, nao seguranca)

Server-side Pydantic e fonte de verdade (Pitfall 5 do research). Client-side apenas antecipa feedback:

- Ao perder foco de `window_end` de leg N, compara com `window_start` de leg N+1. Se invalido, mostra erro inline abaixo do leg N+1 em `--danger-500` com a copy de validacao.
- Badge verde `OK` (ou simplesmente fundo `--success-bg` no fieldset) quando todos os trechos passam validacao temporal local.

### A11y

- Todos os inputs com `<label for>` explicito.
- Botoes `+ Adicionar` e `Remover` com `aria-label` descritivo incluindo numero do trecho (`Adicionar trecho 3`, `Remover trecho 2`).
- Mensagens de erro com `role="alert"` e `aria-live="polite"`.
- `prefers-reduced-motion: reduce` desliga animacoes de adicionar/remover (ja previsto em base.html linha 345).
- Contraste: todas as combinacoes `--text-0/1/2` sobre `--bg-0/1/2` ja validadas no rebrand Orbita (AA minimo).

### Mobile (< 768px)

- Construtor empilha campos em 1 coluna (origin, destination, window_start, window_end, min_stay, max_stay em sequencia).
- Botoes `+ Adicionar` e `Remover` viram full-width.
- Cadeia no card multi quebra em linha propria se > 3 trechos (flex-wrap).
- Preco total mantem 28px mono (nao reduzir — e o elemento focal).

---

## Component Inventory (nesta fase)

Nenhum componente extraido para partial Jinja. Seguindo padrao existente (`dashboard/index.html`, `create.html`), estruturas vivem inline nos templates afetados. Executor pode extrair partials se e somente se houver reuso entre 3+ templates (nao ha: card multi so aparece em `index.html`, breakdown so em `detail.html`, builder so em `create.html`/`edit.html`).

Estruturas HTML novas (declaradas aqui para o planner):

1. **`<section class="mode-toggle">`** em `create.html`/`edit.html` — 2 botoes radio-style
2. **`<section data-mode="multi">`** em `create.html`/`edit.html` — wrapper do construtor, com `<template id="leg-template">`, lista `<div id="legs-container">`, botao `+ Adicionar trecho`
3. **`<fieldset class="leg">`** — cada trecho; segue padrao de input ja existente em `create.html`
4. **`.card.card-multi`** em `index.html` — variante do card com borda esquerda `--accent-500` 3px, badge `MULTI` no canto superior direito, cadeia em linha propria, preco total em mono 28px
5. **`.multi-breakdown`** em `detail.html` — lista de linhas de trecho, separador `--border-2`, rodape com total
6. **Email template** — bloco Jinja em `_render_consolidated_html_multi` com cadeia, total, tabela breakdown, cluster comparadores por trecho

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| shadcn official | nenhum (Jinja2 SSR puro, sem shadcn) | not applicable |
| terceiros | nenhum | not applicable |

Nao ha registry para vet. Todo CSS e inline em `base.html` ou em `<style>` scoped dos templates desta fase, com tokens ja declarados.

---

## Dependencies on Upstream Phases

- **Phase 34 (prediction):** copy e posicionamento da recomendacao reusam 100% o que Phase 34 definir. Esta fase nao redefine copy de recomendacao.
- **Phase 32 (cache):** aviso de quota SerpAPI baixa so aparece se `quota_service` expor endpoint/helper (Pitfall 4 do research). Se nao expor, planner marca como nao-bloqueante.
- **Rebrand Orbita (concluido):** todos os tokens usados ja existem em `base.html`. Nada a adicionar.

---

## Pre-Populated From

| Source | Decisoes usadas |
|--------|----------------|
| `36-CONTEXT.md` | D-07, D-08, D-09, D-10, D-16, D-17, D-18, D-19, D-20 (toggle, builder vanilla, auto-calculo, passageiros globais, card multi, comparadores por trecho, detalhe breakdown, email, subject) |
| `36-RESEARCH.md` | Pattern 4 (builder vanilla), Pitfall 5 (sort antes de validar), Pitfall 7 (guard template) |
| `REQUIREMENTS.md` | MULTI-01..04 (criacao, validacao, busca, sinal sobre total) |
| `CLAUDE.md` (raiz) | Jinja2 SSR puro, pt-BR acentuado, sem emoji, sem travessao, tokens centralizados |
| `app/templates/base.html` | Todos os tokens de spacing, cor, tipografia, radius, elevation |
| Input do usuario (sessao) | Nenhum — tudo pre-populado |

---

## Checker Sign-Off

- [ ] Dimension 1 Copywriting: PASS
- [ ] Dimension 2 Visuals: PASS
- [ ] Dimension 3 Color: PASS
- [ ] Dimension 4 Typography: PASS
- [ ] Dimension 5 Spacing: PASS
- [ ] Dimension 6 Registry Safety: PASS

**Approval:** pending
