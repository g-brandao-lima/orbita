# Phase 33 Summary — Public Route Index (SEO)

**Data:** 2026-04-21
**Duracao:** ~40min
**Status:** SHIPPED (pushado pra master)

## Entregue

### Plan 01 — Core + robots.txt
- [app/services/iata_cities.py](../../../app/services/iata_cities.py) com ~85 IATAs mapeados (BR + internacional principal)
- [app/services/public_route_service.py](../../../app/services/public_route_service.py):
  - `get_route_stats` retorna preco atual (route_cache), mediana 180d, monthly_series, best_months — tudo do banco
  - `has_enough_data` checa threshold de 10 snapshots
- [app/routes/public.py](../../../app/routes/public.py):
  - `GET /rotas/{ORIG}-{DEST}` com Cache-Control 6h, rel=canonical, meta OG/Twitter
  - `GET /robots.txt` liberando `/rotas/*`, sitemap referenciado
- [app/templates/public/route.html](../../../app/templates/public/route.html): hero, historico, melhores meses, CTA "Monitore essa rota"
- AuthMiddleware: adicionadas `/rotas/`, `/sitemap.xml`, `/robots.txt` aos public paths

### Plan 02 — Sitemap + OG image + affiliate
- `GET /sitemap.xml` dinamico listando rotas com >=10 snapshots
- `GET /rotas/{O}-{D}/og-image.png` via Pillow 1200x630 (reusa paleta do Phase 30)
- [app/services/affiliate_links.py](../../../app/services/affiliate_links.py) `build_aviasales_url(marker="714304")`
- Botao "Comprar agora" no template com `rel="nofollow sponsored noopener"`
- `settings.travelpayouts_marker = "714304"` (overridable via env)

### Plan 03 — Internal linking
- `public_route_service.get_top_public_routes(db, limit)` — rotas ordenadas por volume
- Landing deslogada ganhou secao "Rotas populares" (top 3) com links crawlaveis
- Dashboard cards ganharam link "Ver pagina publica" quando rota >=10 snapshots

## Testes

- Antes: 334 passando
- Depois: **369 passando** (+35), 0 regressao
- Novos:
  - 5 iata_cities
  - 6 public_route_service
  - 8 public_route (GET /rotas, /robots.txt)
  - 4 affiliate_links
  - 3 public_sitemap
  - 5 public_og_image
  - 4 public_route_discovery (landing + dashboard linking)

## Commits pushados

- `docs(33): plan Public Route Index SEO (3 plans)`
- `feat(33): public route index SEO (SEO-01..SEO-05)`

## Pos-deploy no Render (auto em ~2min)

- `/rotas/GRU-LIS` vai funcionar imediatamente se ja houver snapshots acumulados (grupos ativos nas rotas seed)
- `/sitemap.xml` vai listar so rotas com historico acumulado suficiente
- `/robots.txt` vai direcionar crawlers
- OG image funciona pra qualquer rota que `get_route_stats` aceitar

## Pos-deploy: a fazer manualmente

1. **Submit sitemap no Google Search Console:**
   - Adicionar propriedade `https://flight-monitor-ly3p.onrender.com`
   - Verificar via meta tag ou DNS
   - Submit sitemap: `https://flight-monitor-ly3p.onrender.com/sitemap.xml`

2. **Aprovacao Aviasales no Travelpayouts:**
   - Dashboard Travelpayouts → Programs → procurar "Aviasales" → Join
   - Sem approval: link funciona, comissao nao e rastreada
   - Com approval: comissao efetiva em compras via redirect

3. **Teste visual ao abrir em producao:**
   - `/rotas/GRU-LIS` — ver hero, historico, CTAs
   - Compartilhar em WhatsApp pra ver preview OG
   - Clicar "Comprar agora" — confirma redirect Aviasales com marker

## Proximo

Phase 34: Price Prediction Engine — "Compre ate DD/MM" baseado em regras deterministicas + backtest retrospectivo.
