# Phase 8: Dashboard Redesign - Context

**Gathered:** 2026-03-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Redesenhar a tela inicial do dashboard com cards coloridos, area de resumo no topo, estado vazio amigavel, e datas em formato brasileiro. Nao altera funcionalidade, apenas visual e UX.

Requisitos: UI-01, UI-02, UI-03, UI-04, UI-05.

</domain>

<decisions>
## Implementation Decisions

### Area de resumo (UI-01)
- **D-01:** Barra no topo com fundo escuro (#1e293b) e texto branco. 3 metricas: "X grupos ativos", "Menor preco: R$X.XXX", "Proximo polling: HH:MM".
- **D-02:** Horizontal em desktop (flex-row), empilhado em mobile (flex-column via media query).
- **D-03:** "Proximo polling" calcula a partir do scheduler (next_run_time). Se indisponivel, mostra "Automatico (1x/dia)".

### Cards de grupo (UI-02, UI-03)
- **D-04:** Card branco com borda esquerda 4px colorida por classificacao:
  - Verde #059669 = LOW (preco bom)
  - Amarelo #d97706 = MEDIUM (preco normal)
  - Vermelho #dc2626 = HIGH (preco alto)
  - Cinza #94a3b8 = sem dados coletados
- **D-05:** Dentro do card: nome do grupo (bold, esquerda), preco mais barato em destaque grande (direita), rota (origem->destino), companhia, datas ida/volta no formato dd/mm/aaaa, badge de sinal.
- **D-06:** Botoes "Editar" e "Ativar/Desativar" discretos no rodape do card.
- **D-07:** Cards inativos com opacidade 0.6 e badge "Inativo".

### Estado vazio (UI-04)
- **D-08:** Icone de aviao SVG simples inline (nao imagem externa).
- **D-09:** Texto: "Nenhum grupo cadastrado. Comece monitorando sua primeira rota!"
- **D-10:** Botao verde "Criar primeiro grupo" que leva para /groups/create.

### Formato de data (UI-05)
- **D-11:** Todas as datas no dashboard (cards, detalhe, grafico) usam dd/mm/aaaa via filtro Jinja2 ou strftime.

### Claude's Discretion
- Espacamento, padding, font-size exatos
- Sombras e border-radius dos cards
- Animacoes sutis (hover)
- Icone SVG exato do aviao

</decisions>

<canonical_refs>
## Canonical References

### Templates atuais (a ser reescritos)
- `app/templates/base.html` - template base com nav e flash messages (manter)
- `app/templates/dashboard/index.html` - lista atual de grupos (reescrever)
- `app/templates/dashboard/detail.html` - pagina de detalhe com Chart.js (atualizar datas)

### Service layer
- `app/services/dashboard_service.py` - get_groups_with_summary, format_price_brl (reusar)
- `app/routes/dashboard.py` - dashboard_index (adicionar dados de resumo ao contexto)

### Requirements
- `.planning/REQUIREMENTS.md` - UI-01, UI-02, UI-03, UI-04, UI-05

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `dashboard_service.get_groups_with_summary()`: ja retorna grupo + snapshot mais barato + sinal mais urgente
- `dashboard_service.format_price_brl()`: formata R$X.XXX,XX
- Flash messages ja funcionam no base.html (Phase 6)
- Chart.js ja carregado no detail.html

### Established Patterns
- CSS inline em tags style nos templates (sem framework CSS)
- Media queries para responsividade em base.html
- Jinja2 template inheritance (base.html -> pages)

### Integration Points
- `dashboard_index` no dashboard.py: adicionar contagem de grupos, menor preco, proximo polling ao contexto
- `app/scheduler.py`: expor next_run_time para o dashboard

</code_context>

<specifics>
## Specific Ideas

- Visual inspirado em dashboards financeiros: limpo, metricas no topo, cards com hierarquia clara
- Preco e a informacao mais importante: deve ser o maior texto no card
- Cores de borda dizem tudo: verde = bom momento, vermelho = caro, cinza = esperando dados

</specifics>

<deferred>
## Deferred Ideas

None - discussion stayed within phase scope.

</deferred>

---

*Phase: 08-dashboard-redesign*
*Context gathered: 2026-03-25 (auto mode)*
