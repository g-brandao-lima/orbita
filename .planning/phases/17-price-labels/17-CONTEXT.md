# Phase 17: Price Labels - Context

**Gathered:** 2026-04-20
**Status:** Implemented

<domain>
Adicionar rotulo "por pessoa, ida e volta" em todos os precos mostrados (dashboard, grafico, emails) e calcular total quando grupo tem mais de 1 passageiro.
</domain>

<decisions>
- Label universal: "por pessoa, ida e volta"
- Total so aparece quando pax > 1 (evita ruido em grupo de 1 pax)
- Email consolidado tem total em linha menor abaixo do preco unitario
- Tooltip do Chart.js mostra total quando pax > 1
- alerts.html atualizado com header explicito "Preco (por pessoa, ida e volta)"
</decisions>

<code_context>
### Arquivos alterados
- app/templates/dashboard/index.html (card preco com label "por pessoa, ida e volta")
- app/templates/dashboard/detail.html (subtitulo no chart + tooltip)
- app/templates/dashboard/alerts.html (header da coluna)
- app/services/alert_service.py (consolidated email + single alert email com helper _price_with_total)
</code_context>

<specifics>
- Formato BRL via format_price_brl (ja existente)
- Middot (&middot;) usado como separador discreto entre per-person e total
</specifics>

<deferred>
None
</deferred>
