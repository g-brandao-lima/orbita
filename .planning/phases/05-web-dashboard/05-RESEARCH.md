# Phase 5: Web Dashboard - Research

**Researched:** 2026-03-25
**Domain:** FastAPI + Jinja2 server-rendered web dashboard with Chart.js
**Confidence:** HIGH

## Summary

Esta fase adiciona uma interface web server-rendered usando FastAPI + Jinja2 templates para visualizar grupos de rota, historico de precos em grafico de linha (Chart.js via CDN), e formularios HTML para criar/editar/desativar grupos. A stack ja esta decidida pelo usuario: sem JS framework, sem build step, sem framework CSS.

O projeto ja possui toda a camada de dados (models, services, CRUD API) implementada nas fases 1-4. O dashboard e essencialmente uma nova camada de apresentacao que consome os mesmos models SQLAlchemy e reutiliza a logica do service layer existente. A unica dependencia nova e Jinja2 (que precisa ser instalada no venv).

**Primary recommendation:** Criar um router separado (`app/routes/dashboard.py`) sem prefix `/api/v1`, usando Jinja2Templates para renderizar HTML. Formularios usam POST padrao com redirect apos sucesso. Chart.js carregado via CDN no template de detalhe do grupo.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Multi-page com navegacao simples (pagina principal = lista de grupos, pagina de detalhe = historico de preco por grupo)
- **D-02:** Formularios de criar/editar grupo em paginas separadas (nao modal)
- **D-03:** Navegacao via links no topo (sem sidebar)
- **D-04:** Chart.js via CDN para grafico de linha do historico de precos (sem npm/build step)
- **D-05:** Grafico mostra ultimas 2 semanas de snapshots para a rota mais barata do grupo
- **D-06:** Formularios HTML padrao com POST para endpoints server-side (Jinja2 renderiza, FastAPI processa)
- **D-07:** Sem JavaScript para submissao de formularios (alinhado com constraint "sem JS framework")
- **D-08:** Badges coloridos por urgencia: cinza (nenhum sinal), amarelo (MEDIA), laranja (ALTA), vermelho (MAXIMA)
- **D-09:** Badge aparece ao lado do nome do grupo na lista principal
- **D-10:** FastAPI + Jinja2 para templates HTML (constraint do PROJECT.md)
- **D-11:** CSS inline ou tag style (sem framework CSS)
- **D-12:** Chart.js e unica dependencia JS, carregada via CDN

### Claude's Discretion
- Estrutura exata dos templates Jinja2 (base.html + pages)
- Estilo visual (cores, espacamento, fontes)
- Mensagens de feedback apos criar/editar/desativar grupo
- Layout responsivo (media queries basicas)

### Deferred Ideas (OUT OF SCOPE)
None
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ALRT-03 | Dashboard web exibe status de todos os grupos ativos e melhor preco atual de cada um | Query FlightSnapshot por route_group_id ordenado por collected_at DESC, primeiro resultado = melhor preco atual; exibido na lista principal |
| DASH-01 | Dashboard lista todos os Grupos de Rota com: melhor preco atual, rota mais barata encontrada e indicador visual de sinal ativo | Query combinada: RouteGroup + subquery FlightSnapshot (min price) + subquery DetectedSignal (urgencia mais alta nas ultimas 12h) |
| DASH-02 | Clicando em um Grupo de Rota abre historico de preco das ultimas 2 semanas em grafico de linha | Query FlightSnapshot WHERE collected_at >= now() - 14 days para a rota mais barata; dados serializados como JSON no template para Chart.js |
| DASH-03 | Dashboard tem formulario para criar novo Grupo de Rota | Formulario HTML com POST, validacao server-side reutilizando logica de RouteGroupCreate schema |
| DASH-04 | Dashboard permite editar e desativar Grupo de Rota existente | Formulario pre-preenchido com GET, POST para atualizar; botao de toggle ativo/inativo |
| DASH-05 | Interface funciona em navegador mobile (layout responsivo simples) | Media queries basicas no CSS inline; layout single-column em telas < 768px |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- **SDD + TDD obrigatorio:** Spec aprovada antes de codigo, testes escritos e falhando (RED) antes de implementacao, implementacao minima (GREEN), refatoracao (REFACTOR)
- **YAGNI estrito:** Nao adicionar nada que nao foi explicitamente pedido
- **Testes AAA/Given-When-Then:** Cobertura de happy path, edge cases, erro esperado
- **Principios FIRST:** Fast, Independent, Repeatable, Self-validating, Timely
- **Checklist de revisao:** DRY, SRP, nomes auto-explicativos, sem console.log/print de debug, complexidade ciclomatica max 5
- **Sem emojis** nas respostas e arquivos
- **Sem travessao** ( -- ) nas respostas

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.115.12 | Web framework (ja instalado) | Ja em uso no projeto |
| Jinja2 | 3.1.6 | Template engine para HTML server-rendered | FastAPI tem integracao nativa via Jinja2Templates |
| SQLAlchemy | 2.0.40 | ORM (ja instalado) | Ja em uso no projeto |
| Chart.js | 4.5.1 | Grafico de linha para historico de precos | Via CDN, unica dependencia JS permitida (D-12) |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python-multipart | (ja incluso em fastapi[standard]) | Parsing de form data para POST | Necessario para Form(...) dependency do FastAPI |

### Alternatives Considered
Nenhuma. Stack esta 100% decidida pelo usuario nas decisoes D-10 a D-12.

**Installation:**
```bash
pip install jinja2==3.1.6
```

Nota: `python-multipart` pode ja estar instalado como dependencia transitiva do FastAPI. Verificar com `pip show python-multipart`. Se nao estiver, instalar:
```bash
pip install python-multipart
```

**Version verification:**
- Jinja2 3.1.6: verificado via `pip index versions jinja2` (latest no PyPI em 2026-03-25)
- Chart.js 4.5.1: verificado via documentacao oficial chartjs.org

## Architecture Patterns

### Recommended Project Structure
```
app/
  routes/
    dashboard.py          # Router para paginas HTML (sem prefix /api/v1)
  templates/
    base.html             # Layout base com nav, meta viewport, style tag
    dashboard/
      index.html          # Lista de grupos (DASH-01, ALRT-03)
      detail.html         # Detalhe do grupo + grafico Chart.js (DASH-02)
      create.html         # Formulario criar grupo (DASH-03)
      edit.html           # Formulario editar grupo (DASH-04)
  services/
    dashboard_service.py  # Queries especificas para dashboard (aggregations)
```

### Pattern 1: Jinja2Templates com FastAPI
**What:** FastAPI fornece `Jinja2Templates` que integra diretamente com path operations
**When to use:** Toda rota que retorna HTML
**Example:**
```python
# Source: https://fastapi.tiangolo.com/advanced/templates/
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db

router = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
def dashboard_index(request: Request, db: Session = Depends(get_db)):
    groups = get_groups_with_summary(db)
    return templates.TemplateResponse(
        request=request,
        name="dashboard/index.html",
        context={"groups": groups},
    )
```

### Pattern 2: Form POST com Redirect (PRG Pattern)
**What:** Post-Redirect-Get previne resubmissao acidental de formularios
**When to use:** Todo formulario de criar/editar/desativar
**Example:**
```python
@router.post("/groups/create")
def create_group_form(
    request: Request,
    name: str = Form(...),
    origins: str = Form(...),
    destinations: str = Form(...),
    duration_days: int = Form(...),
    travel_start: str = Form(...),
    travel_end: str = Form(...),
    target_price: float = Form(None),
    db: Session = Depends(get_db),
):
    # Validar e criar grupo
    # Se erro de validacao, re-renderizar form com mensagem
    # Se sucesso, redirect para lista
    return RedirectResponse(url="/", status_code=303)
```

Nota: `status_code=303` (See Other) e o correto para redirect apos POST em HTTP/1.1.

### Pattern 3: Dados JSON inline para Chart.js
**What:** Serializar dados de preco como JSON no template para Chart.js consumir
**When to use:** Pagina de detalhe do grupo (DASH-02)
**Example:**
```html
<!-- No template detail.html -->
<canvas id="priceChart"></canvas>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.5.1"></script>
<script>
  const ctx = document.getElementById('priceChart').getContext('2d');
  const data = {{ chart_data | tojson }};
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: data.labels,
      datasets: [{
        label: 'Preco (BRL)',
        data: data.prices,
        borderColor: '#2563eb',
        tension: 0.1
      }]
    },
    options: {
      responsive: true,
      scales: { y: { beginAtZero: false } }
    }
  });
</script>
```

### Pattern 4: Template base com heranca Jinja2
**What:** Template base define estrutura HTML, nav, viewport meta, e bloco de conteudo
**When to use:** Todos os templates herdam de base.html
**Example:**
```html
<!-- base.html -->
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}Flight Monitor{% endblock %}</title>
  <style>
    /* CSS inline conforme D-11 */
    body { font-family: system-ui, sans-serif; margin: 0; padding: 0; }
    nav { background: #1e293b; padding: 1rem; }
    nav a { color: white; text-decoration: none; margin-right: 1rem; }
    .container { max-width: 960px; margin: 0 auto; padding: 1rem; }
    @media (max-width: 768px) {
      .container { padding: 0.5rem; }
    }
  </style>
  {% block head %}{% endblock %}
</head>
<body>
  <nav>
    <a href="/">Grupos</a>
    <a href="/groups/create">Novo Grupo</a>
  </nav>
  <div class="container">
    {% block content %}{% endblock %}
  </div>
</body>
</html>
```

### Anti-Patterns to Avoid
- **Duplicar logica de validacao:** Nao reescrever validacao de IATA codes. Reusar a regex `^[A-Z]{3}$` ja existente em `app/schemas.py`.
- **Fazer queries na rota:** Manter queries no service layer (`dashboard_service.py`), rotas sao thin controllers.
- **Retornar JSON de rotas HTML:** Todas as rotas do dashboard devem retornar HTMLResponse ou RedirectResponse, nunca JSON.
- **JavaScript para form submission:** Decisao D-07 proibe JS para submissao. Usar action/method HTML nativo.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Template rendering | String concatenation de HTML | Jinja2Templates do FastAPI | XSS protection via auto-escaping, heranca de templates |
| Form data parsing | Manual request body parsing | FastAPI Form(...) + python-multipart | Type conversion automatica, erros claros |
| Chart rendering | Canvas API manual ou SVG | Chart.js 4.5.1 via CDN | Responsivo, tooltips, animacoes, manutencao zero |
| Redirect apos POST | Response com header Location manual | RedirectResponse(status_code=303) | FastAPI wrapper correto, evita bugs de status code |
| URL generation em templates | Strings hardcoded de URL | url_for() do Jinja2/Starlette | Refactoring-safe, funciona com prefixes |

**Key insight:** O projeto ja tem toda a logica de negocio no service layer. O dashboard e puramente uma camada de apresentacao que traduz dados existentes para HTML.

## Common Pitfalls

### Pitfall 1: Jinja2 nao instalado
**What goes wrong:** FastAPI importa `Jinja2Templates` mas Jinja2 nao esta no venv. Erro no import.
**Why it happens:** Jinja2 NAO esta instalado no venv atual do projeto (verificado).
**How to avoid:** Instalar `jinja2==3.1.6` e `python-multipart` antes de qualquer codigo.
**Warning signs:** `ModuleNotFoundError: No module named 'jinja2'`

### Pitfall 2: python-multipart ausente para Form()
**What goes wrong:** FastAPI Form(...) dependency requer python-multipart. Sem ele, erro em runtime ao processar POST de formulario.
**Why it happens:** python-multipart nao e dependencia direta do FastAPI base.
**How to avoid:** Instalar `python-multipart` junto com Jinja2.
**Warning signs:** `RuntimeError: Form data requires "python-multipart" to be installed.`

### Pitfall 3: Esquecer status_code=303 no redirect apos POST
**What goes wrong:** Com redirect 302, alguns browsers re-enviam POST ao inves de fazer GET.
**Why it happens:** HTTP 302 e ambiguo sobre metodo do redirect. HTTP 303 garante GET.
**How to avoid:** Sempre usar `RedirectResponse(url="/", status_code=303)` apos POST.
**Warning signs:** Formulario cria duplicatas ao usar "voltar" no browser.

### Pitfall 4: Chart.js nao renderiza com dados vazios
**What goes wrong:** Se o grupo nao tem snapshots (grupo recem-criado), Chart.js renderiza canvas vazio sem mensagem.
**Why it happens:** Chart.js nao exibe mensagem padrao quando datasets estao vazios.
**How to avoid:** Checar `if chart_data.prices` no template e exibir mensagem "Nenhum dado coletado ainda" quando vazio.
**Warning signs:** Pagina de detalhe mostra area em branco sem explicacao.

### Pitfall 5: IATA codes em lowercase no formulario
**What goes wrong:** Usuario digita "gru" e validacao rejeita (regex exige uppercase).
**Why it happens:** Formulario HTML nao forca uppercase automaticamente.
**How to avoid:** Converter para uppercase no server antes de validar. Ou usar `style="text-transform: uppercase"` no input como hint visual.
**Warning signs:** Erros de validacao frustrantes para o usuario.

### Pitfall 6: Origins/destinations como campo unico no form
**What goes wrong:** O modelo espera `list[str]` para origins/destinations, mas form HTML envia string unica.
**Why it happens:** HTML form nao tem conceito nativo de lista. Um input text envia uma string.
**How to avoid:** Aceitar string separada por virgulas no form (ex: "GRU,CGH") e fazer split server-side antes de validar.
**Warning signs:** Erro de tipo ao tentar salvar no banco.

## Code Examples

### Query: Grupos com melhor preco e sinal ativo (DASH-01)
```python
# Source: padrao SQLAlchemy 2.0 com subqueries
from sqlalchemy import func, select, and_
from datetime import datetime, timedelta

def get_groups_with_summary(db: Session) -> list[dict]:
    """Retorna todos os grupos com melhor preco atual e sinal mais urgente."""
    groups = db.query(RouteGroup).all()
    result = []
    for group in groups:
        # Melhor preco: snapshot mais recente com menor preco
        latest_snapshot = (
            db.query(FlightSnapshot)
            .filter(FlightSnapshot.route_group_id == group.id)
            .order_by(FlightSnapshot.collected_at.desc())
            .first()
        )
        # Cheapest snapshot do ultimo ciclo de coleta
        cheapest = None
        if latest_snapshot:
            cycle_time = latest_snapshot.collected_at
            cheapest = (
                db.query(FlightSnapshot)
                .filter(
                    FlightSnapshot.route_group_id == group.id,
                    FlightSnapshot.collected_at == cycle_time,
                )
                .order_by(FlightSnapshot.price.asc())
                .first()
            )
        # Sinal ativo: mais urgente nas ultimas 12h
        recent_signal = (
            db.query(DetectedSignal)
            .filter(
                DetectedSignal.route_group_id == group.id,
                DetectedSignal.detected_at >= datetime.utcnow() - timedelta(hours=12),
            )
            .order_by(
                # MAXIMA > ALTA > MEDIA
                func.case(
                    (DetectedSignal.urgency == "MAXIMA", 3),
                    (DetectedSignal.urgency == "ALTA", 2),
                    (DetectedSignal.urgency == "MEDIA", 1),
                    else_=0,
                ).desc()
            )
            .first()
        )
        result.append({
            "group": group,
            "cheapest_snapshot": cheapest,
            "signal": recent_signal,
        })
    return result
```

### Query: Historico de precos para grafico (DASH-02)
```python
def get_price_history(db: Session, group_id: int, days: int = 14) -> dict:
    """Retorna labels (datas) e prices para Chart.js."""
    cutoff = datetime.utcnow() - timedelta(days=days)

    # Encontrar rota mais barata do grupo
    cheapest_route = (
        db.query(
            FlightSnapshot.origin,
            FlightSnapshot.destination,
        )
        .filter(FlightSnapshot.route_group_id == group_id)
        .group_by(FlightSnapshot.origin, FlightSnapshot.destination)
        .order_by(func.min(FlightSnapshot.price).asc())
        .first()
    )
    if not cheapest_route:
        return {"labels": [], "prices": []}

    snapshots = (
        db.query(FlightSnapshot)
        .filter(
            FlightSnapshot.route_group_id == group_id,
            FlightSnapshot.origin == cheapest_route[0],
            FlightSnapshot.destination == cheapest_route[1],
            FlightSnapshot.collected_at >= cutoff,
        )
        .order_by(FlightSnapshot.collected_at.asc())
        .all()
    )
    return {
        "labels": [s.collected_at.strftime("%d/%m %Hh") for s in snapshots],
        "prices": [s.price for s in snapshots],
        "route": f"{cheapest_route[0]} -> {cheapest_route[1]}",
    }
```

### Template: Badge de urgencia (D-08)
```html
<!-- Jinja2 macro para badge de sinal -->
{% macro signal_badge(signal) %}
  {% if signal is none %}
    <span style="background:#94a3b8;color:white;padding:2px 8px;border-radius:4px;font-size:0.8rem;">Sem sinal</span>
  {% elif signal.urgency == "MEDIA" %}
    <span style="background:#eab308;color:white;padding:2px 8px;border-radius:4px;font-size:0.8rem;">MEDIA</span>
  {% elif signal.urgency == "ALTA" %}
    <span style="background:#f97316;color:white;padding:2px 8px;border-radius:4px;font-size:0.8rem;">ALTA</span>
  {% elif signal.urgency == "MAXIMA" %}
    <span style="background:#ef4444;color:white;padding:2px 8px;border-radius:4px;font-size:0.8rem;">MAXIMA</span>
  {% endif %}
{% endmacro %}
```

### Form: Criar grupo com campos de lista (DASH-03)
```html
<form method="POST" action="/groups/create">
  <label>Nome do Grupo</label>
  <input type="text" name="name" required>

  <label>Origens (codigos IATA separados por virgula)</label>
  <input type="text" name="origins" placeholder="GRU,CGH" required
         style="text-transform: uppercase;">

  <label>Destinos (codigos IATA separados por virgula)</label>
  <input type="text" name="destinations" placeholder="LIS,OPO" required
         style="text-transform: uppercase;">

  <label>Duracao da viagem (dias)</label>
  <input type="number" name="duration_days" min="1" required>

  <label>Inicio do periodo</label>
  <input type="date" name="travel_start" required>

  <label>Fim do periodo</label>
  <input type="date" name="travel_end" required>

  <label>Preco-alvo (opcional)</label>
  <input type="number" name="target_price" step="0.01">

  <button type="submit">Criar Grupo</button>
</form>
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Jinja2Templates(directory=...) passando request como context | Jinja2Templates passando request como parametro nomeado | FastAPI 0.108+ | `templates.TemplateResponse(request=request, name=..., context=...)` e o padrao atual |
| Chart.js 3.x com imports separados | Chart.js 4.x com auto-register de todos os controllers | Chart.js 4.0 (2023) | CDN single-file funciona sem registrar controllers manualmente |

**Deprecated/outdated:**
- `templates.TemplateResponse("template.html", {"request": request})`: formato antigo. Usar `templates.TemplateResponse(request=request, name="template.html", context={})` (parametros nomeados).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3.5 |
| Config file | Nenhum arquivo de config dedicado; conftest.py em tests/ |
| Quick run command | `python -m pytest tests/test_dashboard.py -x -q` |
| Full suite command | `python -m pytest tests/ -x -q` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ALRT-03 | GET / retorna HTML com lista de grupos, preco atual e sinais | integration | `python -m pytest tests/test_dashboard.py::test_index_shows_groups_with_price_and_signal -x` | Wave 0 |
| DASH-01 | Lista mostra nome, melhor preco, rota mais barata, badge de sinal | integration | `python -m pytest tests/test_dashboard.py::test_index_group_summary -x` | Wave 0 |
| DASH-02 | GET /groups/{id} retorna HTML com dados JSON para Chart.js | integration | `python -m pytest tests/test_dashboard.py::test_detail_chart_data -x` | Wave 0 |
| DASH-03 | POST /groups/create cria grupo e redireciona para / | integration | `python -m pytest tests/test_dashboard.py::test_create_group_form -x` | Wave 0 |
| DASH-04 | POST /groups/{id}/edit atualiza grupo; POST /groups/{id}/toggle alterna ativo | integration | `python -m pytest tests/test_dashboard.py::test_edit_group_form -x` | Wave 0 |
| DASH-05 | Paginas tem meta viewport e CSS responsivo | unit | `python -m pytest tests/test_dashboard.py::test_responsive_meta_viewport -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/test_dashboard.py -x -q`
- **Per wave merge:** `python -m pytest tests/ -x -q`
- **Phase gate:** Full suite green antes de verify-work

### Wave 0 Gaps
- [ ] `tests/test_dashboard.py` - cobre ALRT-03, DASH-01 a DASH-05
- [ ] `tests/test_dashboard_service.py` - cobre queries de aggregation (get_groups_with_summary, get_price_history)
- [ ] Instalacao: `pip install jinja2==3.1.6 python-multipart` - se nao detectados no venv

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Runtime | Sim | 3.x (venv ativo) | Nenhum |
| FastAPI | Web framework | Sim | 0.115.12 | Nenhum |
| Jinja2 | Templates HTML | Nao | Nao instalado no venv | Instalar: pip install jinja2==3.1.6 |
| python-multipart | Form parsing | A verificar | A verificar | Instalar: pip install python-multipart |
| Chart.js | Graficos | Sim (CDN) | 4.5.1 | Nenhuma instalacao local necessaria |
| pytest | Testes | Sim | 8.3.5 | Nenhum |
| SQLite | Banco de dados | Sim | Embutido | Nenhum |

**Missing dependencies with no fallback:**
- Nenhum bloqueante. Todas as dependencias faltantes podem ser instaladas.

**Missing dependencies with fallback:**
- Jinja2: instalar via pip (obrigatorio para a fase)
- python-multipart: instalar via pip (obrigatorio para Form())

## Open Questions

1. **Formato de exibicao de preco**
   - What we know: FlightSnapshot armazena price como float e currency como "BRL"
   - What's unclear: Formatar como "R$ 3.500,00" (pt-BR) ou manter simples "3500.00"?
   - Recommendation: Usar filtro Jinja2 customizado para formatar como "R$ X.XXX,XX" (locale pt-BR). Simples de implementar com `f"R$ {price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")`

2. **Ciclo de coleta vs snapshot individual para "melhor preco atual"**
   - What we know: Cada ciclo de polling gera multiplos snapshots com collected_at similar
   - What's unclear: Agrupar por collected_at exato ou por janela de tempo?
   - Recommendation: Pegar o snapshot mais recente (ORDER BY collected_at DESC LIMIT 1) e depois todos os snapshots com aquele mesmo collected_at para encontrar o mais barato. Isso identifica o ciclo mais recente naturalmente.

## Sources

### Primary (HIGH confidence)
- FastAPI official docs: https://fastapi.tiangolo.com/advanced/templates/ - Setup de Jinja2Templates, TemplateResponse, StaticFiles
- Chart.js official docs: https://www.chartjs.org/docs/latest/getting-started/ - CDN setup, line chart config
- Codebase existente: `app/models.py`, `app/routes/route_groups.py`, `app/schemas.py`, `tests/conftest.py` - patterns e estrutura do projeto

### Secondary (MEDIUM confidence)
- PyPI: Jinja2 3.1.6 latest (verificado via pip index)
- jsDelivr CDN: Chart.js 4.5.1 (verificado via chartjs.org docs)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - stack decidida pelo usuario, versoes verificadas no PyPI e CDN
- Architecture: HIGH - FastAPI + Jinja2 e padrao bem documentado; projeto ja segue patterns claros
- Pitfalls: HIGH - pitfalls verificados contra documentacao oficial e estado atual do venv

**Research date:** 2026-03-25
**Valid until:** 2026-04-25 (stack estavel, sem mudancas breaking esperadas)
