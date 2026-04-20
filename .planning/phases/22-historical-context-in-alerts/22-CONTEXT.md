# Phase 22: Historical Context in Alerts - Context

**Gathered:** 2026-04-20
**Status:** Implemented

<domain>
Adicionar contexto quantitativo nos alertas: "X% abaixo da media dos ultimos 90 dias (N amostras)". Gap identificado na pesquisa de mercado: nenhum concorrente BR entrega contexto historico.
</domain>

<decisions>
- Janela: 90 dias (compromisso entre ruido e relevancia)
- min_samples = 10 (abaixo disso, dados nao sao significativos)
- Threshold: so mostra "abaixo" se for <=-5%, so "acima" se for >=5%, senao "em linha"
- Implementacao server-side: get_historical_price_context em snapshot_service
- Email renderer aceita parametro opcional historical_ctx
- compose_consolidated_email aceita opcional db Session para buscar contexto
</decisions>

<code_context>
### Arquivos alterados
- app/services/snapshot_service.py: get_historical_price_context
- app/services/alert_service.py: _format_historical_context, params historical_ctx
- app/services/polling_service.py: passa db para compose_consolidated_email
- tests/test_historical_context.py: 6 testes (samples, stats, format below/above/inline/none)
</code_context>

<specifics>
- Frase usada no email destaca-se com fundo claro translucido
- Formato neutro ("em linha") evita alarme desnecessario quando preco e medio
</specifics>

<deferred>
- Tendencia temporal (caindo vs subindo) alem da media absoluta: futuro
- Sazonalidade (media mesmo mes ano passado): precisa mais dados historicos
</deferred>
