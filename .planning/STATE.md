---
gsd_state_version: 1.0
milestone: v2.4 (planning)
milestone_name: TBD
status: between_milestones
stopped_at: v2.3 shipped 2026-04-24, quick fixes 260423-1fg + 260425-0sf aplicados, aguardando /gsd:new-milestone v2.4
last_updated: "2026-04-25T03:45:00.000Z"
last_activity: 2026-04-25
progress:
  total_phases: 0
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-21)

**Core value:** Detectar o momento certo de comprar uma passagem antes que o preco suba, apresentando o preco de forma clara e imediata para o usuario tomar decisao rapida.
**Current focus:** Aguardando definicao do v2.4 via /gsd:new-milestone

## Current Position

Milestone: v2.3 encerrado (shipped 2026-04-24, tag v2.3)
Status: between milestones, sem fase ativa
Quick tasks recentes: 260423-1fg (hero carousel), 260425-0sf (fix quota + cache expandido + copy)
Seeds dormindo: SEED-001 (multi-city hub-and-spoke)
Last activity: 2026-04-25

Pendencias antes do v2.4:
- Deploy do quick-260425-0sf em producao (commits no GitHub, falta `fly deploy`)
- UAT manual do fix quota (clicar Buscar agora com quota=0 e ver flash novo)

Candidatos para o v2.4 (a confirmar via /gsd:new-milestone):
- Dominio proprio (orbita.com.br ou similar)
- Cloudflare CDN
- Filtro do hero carousel por sinal ativo
- Multi-city hub-and-spoke (SEED-001) — surfa automaticamente

## Performance Metrics

**Velocity:**

- Total plans completed (cumulative): 32
- Average duration: ~3min
- Total execution time: ~100min

## Accumulated Context

### Roadmap Evolution

- v2.3 started from .planning/milestones/v2.3-PROPOSAL.md approved 2026-04-21
- Shared Groups droppada (caso de uso pequeno, dois Google logins resolvem)
- Multi-trecho movido de v2.4 pra v2.3 como fase final (Phase 36)
- Cache Layer Travelpayouts adicionada como pre-requisito (Phase 32)
- Phase 31.9 criada como hygiene quick win (decimal insertion, roda antes da 32)

### Decisions

- [v2.3, 2026-04-21]: Travelpayouts Data API como fonte de bulk caching (free, monetiza via affiliate)
- [v2.3, 2026-04-21]: SerpAPI mantida apenas pra refresh on-demand de grupo ativo
- [v2.3, 2026-04-21]: fast-flights removido (scraping fragil, retorna vazio silenciosamente)
- [v2.3, 2026-04-21]: Preco exibido como "preco de referencia" com disclaimer de ate 5% divergencia
- [v2.3, 2026-04-21]: Prediction deterministica (sem ML) ate ter >=6 meses de dados reais
- [v2.3, 2026-04-21]: Onboarding wizard (Phase 35) condicional — so executar com >=3 usuarios organicos da Phase 33

### Pending Todos

- Cadastrar conta Travelpayouts e obter TRAVELPAYOUTS_TOKEN (bloqueador antes da Phase 32)
- Formalizar regra de negocio multi-trecho via /gsd:discuss-phase 36 quando chegar o momento

### Blockers/Concerns

- [Phase 32]: Travelpayouts account + token obrigatorios antes de comecar
- [Phase 33]: Monetizacao via affiliate depende de aprovacao Travelpayouts
- [Phase 35]: Condicional ao resultado da Phase 33 (minimo 3 usuarios organicos)
- [Phase 36]: Regra de negocio multi-trecho a formalizar via /gsd:discuss-phase 36

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 260423-1fg | Hero card carousel na landing com top 6 rotas do route_cache | 2026-04-23 | 3880e48 | [260423-1fg-hero-card-carousel-na-landing-com-top-6-](./quick/260423-1fg-hero-card-carousel-na-landing-com-top-6-/) |
| 260425-0sf | Fix quota esgotada + cache Travelpayouts expandido + copy | 2026-04-25 | 28974df | [260425-0sf-fix-quota-esgotada-cache-travelpayouts-e](./quick/260425-0sf-fix-quota-esgotada-cache-travelpayouts-e/) |

## Session Continuity

Last session: 2026-04-23T03:36:07.149Z
Stopped at: Completed 36-04-PLAN.md
Resume file: None
