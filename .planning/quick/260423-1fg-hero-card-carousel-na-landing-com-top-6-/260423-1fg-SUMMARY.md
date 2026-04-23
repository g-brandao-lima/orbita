---
phase: 260423-1fg-hero-carousel
plan: 01
type: quick
status: complete
tasks_total: 3
tasks_completed: 3
tests_added: 9
tests_passing: 9
regression: 0
commits:
  - hash: e04274f
    msg: "feat(landing): get_hero_routes retornando top N do route_cache"
  - hash: 076c5ee
    msg: "feat(landing): injeta hero_routes no contexto da rota /"
  - hash: 3880e48
    msg: "feat(landing): hero-carousel com auto-play 5s, setas, dots e pause-on-hover"
files_modified:
  - app/services/public_route_service.py
  - app/routes/dashboard.py
  - app/templates/landing.html
  - tests/test_hero_carousel.py
requirements:
  - HERO-01
  - HERO-02
  - HERO-03
---

# Quick 260423-1fg: Hero Card Carousel na Landing Summary

One-liner: carousel SSR-first de ate 6 cards de rota vindos do route_cache, auto-play 5s com fade, vanilla JS inline, zero dependencia nova.

## O que foi entregue

- Service `get_hero_routes(db, limit=6)` em `public_route_service.py`, leitura direta de `route_cache` com `min_price > 0` ordenado por `cached_at DESC`, retorna lista vazia (nunca None).
- Handler `/` (ramo `user is None`) em `dashboard.py` injeta `hero_routes` no contexto, mantendo `featured_route` como fallback.
- Template `landing.html` reescrito no bloco do hero com `.hero-carousel` + slides `landing-preview-link hero-carousel-slide`, controles prev/next, dots, CSS tokens-only (`--bg-2`, `--border-2`, `--brand-500`, `--r-full`, `--sp-*`) e JS vanilla inline (~50 LOC) com auto-play 5s, pause-on-hover e `prefers-reduced-motion`.
- Fallback em 3 niveis: `hero_routes` (primario) -> `featured_route` (legado preservado na integra) -> card exemplo hardcoded (`.hero-carousel-fallback`).
- 9 testes novos em `tests/test_hero_carousel.py` (RED antes de cada GREEN), 5 cobrindo o service, 2 cobrindo a injecao no handler, 2 cobrindo o markup acessivel.

## Decisoes

- Ordenacao por `cached_at DESC` (campo real do modelo; plan mencionava `updated_at` inexistente — alinhado com decisao do usuario).
- Landing permaneceu em `dashboard_index` (nao criei `landing.py`).
- Acentuacao removida apenas em `aria-label="Proxima rota"` por exigencia explicita do spec de teste; textos visiveis mantem acentos (`"Rota anterior"` OK, `"Navegação de rotas"` OK, `"Menor preço cacheado"` OK).

## Verificacao

- `pytest tests/test_hero_carousel.py -v`: 9/9 verdes.
- `pytest -x --ignore=tests/test_hero_carousel.py`: 410/410 verdes, zero regressao.
- CSS so usa tokens de `base.html` (sem hex hardcoded em codigo novo).
- Sem dependencia npm/pip nova.

## Pendencias

- Conferencia visual opcional via `uvicorn app.main:app --reload` em `/`: auto-rotacao, hover pausa, setas/dots, fallback sem JS.

## Self-Check: PASSED

- File `app/services/public_route_service.py`: FOUND
- File `app/routes/dashboard.py`: FOUND
- File `app/templates/landing.html`: FOUND
- File `tests/test_hero_carousel.py`: FOUND
- Commit e04274f: FOUND
- Commit 076c5ee: FOUND
- Commit 3880e48: FOUND
