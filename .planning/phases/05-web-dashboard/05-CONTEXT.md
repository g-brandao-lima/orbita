# Phase 5: Web Dashboard - Context

**Gathered:** 2026-03-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Interface web que permite visualizar o estado atual de todos os grupos, historico de precos em grafico de linha, e gerenciar grupos (criar, editar, desativar) pelo navegador. Interface em portugues, simples e funcional, responsiva para mobile.

Requisitos: ALRT-03, DASH-01, DASH-02, DASH-03, DASH-04, DASH-05.

</domain>

<decisions>
## Implementation Decisions

### Layout structure
- **D-01:** Multi-page com navegacao simples (pagina principal = lista de grupos, pagina de detalhe = historico de preco por grupo)
- **D-02:** Formularios de criar/editar grupo em paginas separadas (nao modal)
- **D-03:** Navegacao via links no topo (sem sidebar)

### Price chart
- **D-04:** Chart.js via CDN para grafico de linha do historico de precos (sem npm/build step)
- **D-05:** Grafico mostra ultimas 2 semanas de snapshots para a rota mais barata do grupo

### Form handling
- **D-06:** Formularios HTML padrao com POST para endpoints server-side (Jinja2 renderiza, FastAPI processa)
- **D-07:** Sem JavaScript para submissao de formularios (alinhado com constraint "sem JS framework")

### Signal indicators
- **D-08:** Badges coloridos por urgencia: cinza (nenhum sinal), amarelo (MEDIA), laranja (ALTA), vermelho (MAXIMA)
- **D-09:** Badge aparece ao lado do nome do grupo na lista principal

### Tecnologia
- **D-10:** FastAPI + Jinja2 para templates HTML (constraint do PROJECT.md)
- **D-11:** CSS inline ou tag style (sem framework CSS — manter simples)
- **D-12:** Chart.js e unica dependencia JS, carregada via CDN

### Claude's Discretion
- Estrutura exata dos templates Jinja2 (base.html + pages)
- Estilo visual (cores, espacamento, fontes)
- Mensagens de feedback apos criar/editar/desativar grupo
- Layout responsivo (media queries basicas)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing API routes (reuse for form processing)
- `app/routes/route_groups.py` — CRUD endpoints existentes (POST, PUT, PATCH, DELETE)
- `app/routes/alerts.py` — Silence endpoint com HMAC token
- `app/schemas.py` — RouteGroupCreate, RouteGroupUpdate, RouteGroupResponse

### Models and data layer
- `app/models.py` — RouteGroup, FlightSnapshot, DetectedSignal (queries para dashboard)
- `app/database.py` — SessionLocal, get_db dependency
- `app/services/serpapi_client.py` — SerpApiClient (referencia para entender dados coletados)

### Project constraints
- `.planning/REQUIREMENTS.md` — ALRT-03, DASH-01 a DASH-05
- `.planning/ROADMAP.md` — Phase 5 success criteria

### Entry point
- `main.py` — FastAPI app, lifespan, router registration

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `app/routes/route_groups.py`: CRUD API completo — dashboard forms podem reusar a logica de service layer
- `app/models.py`: FlightSnapshot tem price, collected_at, route_group_id — query direta para grafico
- `app/models.py`: DetectedSignal tem signal_type, urgency — query para badges de sinal ativo
- `app/schemas.py`: Pydantic schemas ja validam dados de RouteGroup — forms podem usar mesma validacao

### Established Patterns
- Router pattern: APIRouter com prefix, registrado em main.py via include_router
- Service layer: logica de negocio em app/services/, routes sao thin controllers
- Database: get_db dependency injection via Depends()

### Integration Points
- `main.py`: registrar novo router para paginas HTML (sem prefix /api/v1)
- Templates: criar app/templates/ com Jinja2 templates
- Static: criar app/static/ para CSS se necessario (ou inline)
- Chart.js: CDN no template base, dados passados como JSON no template de detalhe

</code_context>

<specifics>
## Specific Ideas

- Interface em portugues (labels, mensagens, navegacao)
- Grafico de preco deve ser simples: eixo X = data/hora, eixo Y = preco em BRL
- Lista de grupos deve mostrar rapidamente qual grupo tem alerta ativo e qual e o preco mais recente
- Formulario de criar grupo deve validar IATA codes (3 letras maiusculas)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 05-web-dashboard*
*Context gathered: 2026-03-25 (auto mode)*
