---
id: SEED-001
status: dormant
planted: 2026-04-25
planted_during: v2.3 post-completion (entre milestones)
trigger_when: v2.4 abrir, antes de domain proprio + Cloudflare
scope: Medium
---

# SEED-001: Multi-city automatico com hub-and-spoke

## Why This Matters

Caso de uso real validado em 2026-04-25: usuario tentou criar grupos REC/JPA/CPV -> SCL (Santiago) no orbita-flights.fly.dev e nenhum snapshot foi criado. Investigacao via /gsd:debug revelou tres camadas de bug, sendo a ultima: **nao existe voo direto Nordeste-internacional, e a Orbita so busca trechos diretos**. SerpAPI retornou vazio em todos os 36 pares (3 origens x 12 datas).

A Phase 36 (multi-leg) entrega roteiro turistico encadeado com estadia em cada perna (BR -> Italia -> Espanha -> BR como mochilao europeu), mas nao resolve o caso de **uma viagem so com conexao automatica** (REC -> GRU -> SCL ida e volta).

Sem isso, qualquer rota fora das top 28 BR+Europa cobertas por voo direto sai vazia. Limita drasticamente o publico-alvo (viajante BR no Nordeste com destino LatAm).

## When to Surface

**Trigger:** ativar quando v2.4 abrir, antes de domain proprio + Cloudflare

Apresentar durante `/gsd:new-milestone v2.4` quando o escopo mencionar:
- Cobertura de rotas / acquisition organico
- Publico-alvo Nordeste ou regional BR
- Reducao de "buscas vazias" / dead ends do funil
- Multi-trecho real (diferenciar de Phase 36)

## Scope Estimate

**Medium** — uma fase ou duas. Cabe um quick fix A previo (poucas horas) e uma fase formal B depois.

### Tres opcoes de implementacao

**A. Habilitar `max_stops=1` no SerpAPI client (Quick fix, ~1h)**
- O field `max_stops` ja existe no model RouteGroup
- Forcar `max_stops=1` na chamada SerpAPI quando rota nao-direta (cache miss em route_cache)
- SerpAPI retorna voos com conexao operados pela mesma cia (bilhete unico, ex: Latam REC-GRU-SCL)
- **Limitacao:** so resolve quando a cia tem conexao no proprio voo. Se nao tem (rota muito exotica), continua vazio
- Implementavel via `/gsd:quick`

**B. Hub-and-spoke automatico (Fase formal)**
- Quando rota direta + max_stops=1 retornam vazio, sistema detecta e busca **REC -> GRU + GRU -> SCL no mesmo dia**, soma os precos, exibe "via GRU"
- Funciona mesmo se cias forem diferentes (usuario compra 2 bilhetes)
- Mapear hubs por regiao: Nordeste -> GRU/GIG; Sul -> GRU/CWB; Norte -> GRU/BSB
- Validar com 1 dia minimo entre os dois trechos, alertar quando bagagem nao despacha automatica
- Diferenciar visualmente no card ("via GRU, 2 bilhetes")

**C. Travelpayouts `prices_for_dates` multi-segment (Alto custo)**
- A API Travelpayouts tem endpoint que aceita multiplos segmentos numa busca
- Substituir cliente atual usaria isso pra rotas exoticas
- Mexe na fonte de dados, requer revisao de schema
- Adiar para v3.x se nunca virar prioridade

### Recomendacao de execucao

1. **Quick fix A primeiro** via `/gsd:quick "habilitar max_stops=1 em rotas com cache miss"`. Investigar se SerpAPI retorna boas rotas (~1 manha).
2. Se A resolve >=80% dos casos, parar ai e adiar B.
3. Se A insuficiente, **fase formal B** com plan de hub-and-spoke. Prerequisito: dataset de hubs por regiao + UX de "via X" no card.
4. Manter REC/JPA/CPV->internacional em known issues do README ate B existir.

## Breadcrumbs

Codigo relevante atual:

- `app/services/flight_search.py:49` — `search_flights_ex` (cache-first com fallback SerpAPI)
- `app/services/serpapi_client.py` — onde `max_stops` precisa ser injetado
- `app/services/multi_leg_service.py` — Phase 36, NAO confundir (e diferente)
- `app/models.py` — `RouteGroup.max_stops` existe mas nao tem UI exposta
- `app/services/route_cache_service.py:127` — TOP_BR_ROUTES, lista expandida em quick-260425-0sf
- `.planning/debug/resolved/silent-manual-polling.md` — debug session que originou esta seed
- `.planning/quick/260425-0sf-fix-quota-esgotada-cache-travelpayouts-e/260425-0sf-SUMMARY.md` — quick task que adicionou cache pra GRU-SCL/EZE/LIM/BOG/MEX (mitigacao parcial: rotas direto saem do cache, mas Nordeste continua sem solucao)

## Notes

- Phase 36 multi-leg builder NAO substitui isso. Workaround atual pro user: criar 2 grupos (REC->GRU + GRU->SCL).
- README.md ja menciona "Roundtrip only" como limitacao — atualizar quando B for entregue.
- Quota SerpAPI mensal (250) pode estourar mais rapido com max_stops=1 (mais resultados por busca). Monitorar antes/depois de A.
- Considerar tambem rotas inversas (SCL->REC) que tem o mesmo problema simetrico.
