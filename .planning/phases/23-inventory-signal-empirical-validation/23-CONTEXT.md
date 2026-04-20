# Phase 23: Inventory Signal Empirical Validation - Context

**Gathered:** 2026-04-20
**Status:** Implemented (ferramenta criada, resultado real depende de dados em producao)

<domain>
Ferramenta de analise para validar se os sinais emitidos realmente preveem variacao de preco. Justifica ou refuta claims de marketing sobre o valor dos alertas.

**Nota:** O sinal original K/Q/V (BALDE FECHANDO) foi removido na Phase 21 junto com BookingClassSnapshot. Os sinais atuais analisados sao os baseados em preco: LOW_PRICE_DETECTED, WINDOW_OPTIMAL, etc.
</domain>

<decisions>
- Script ad-hoc em scripts/analyze_signals.py (nao roda em ciclo de polling)
- Metrica por tipo de sinal:
  - avg_delta_pct em 3/7/14 dias apos deteccao
  - hit_rate por definicao do tipo (ver abaixo)
- Definicoes de "acerto":
  - Sinais tipo "buy now" (LOW_PRICE_DETECTED, BALDE_FECHANDO, BALDE_REABERTO): acerto = preco SUBIU apos
  - Sinais informativos: acerto = preco se manteve (nao caiu >10%)
- Saida: JSON por tipo, para facilitar threshold de decisao
- Teste em tests/test_analyze_signals.py cobre fluxo com dados sinteticos

## Como rodar
```
DATABASE_URL=postgresql://... python scripts/analyze_signals.py
```

## Thresholds de decisao
- hit_rate_7d >= 70% -> sinal validado, usar como marketing defensavel
- hit_rate_7d entre 50% e 70% -> sinal util mas com ressalva, evitar claims absolutos
- hit_rate_7d < 50% -> sinal nao ajuda, remover ou reformular
</decisions>

<code_context>
### Arquivos novos
- scripts/analyze_signals.py
- tests/test_analyze_signals.py (2 testes)
</code_context>

<specifics>
- Script so produz resultados uteis apos ciclos de polling suficientes em producao
- Executar ao completar ~1 mes de polling continuo em producao com varios usuarios
</specifics>

<deferred>
- Integracao no dashboard (mostrar accuracy ao usuario): futuro
- Auto-calibrar thresholds do signal_service baseado nos resultados: futuro
</deferred>
