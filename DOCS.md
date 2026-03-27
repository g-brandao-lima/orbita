# Flight Monitor - Documentação Técnica

## O que é

Sistema pessoal de monitoramento de passagens aéreas que busca preços automaticamente, detecta oportunidades de compra, e envia alertas por email. Interface web dark mode para visualizar grupos, preços e sinais.

---

## Stack Tecnológica

| Camada | Tecnologia | Versão | Pra quê |
|--------|-----------|--------|---------|
| Backend | Python + FastAPI | 3.13 / 0.115 | API e servidor web |
| Banco | SQLite via SQLAlchemy | 2.0.40 | Armazenamento (arquivo único) |
| Frontend | Jinja2 + HTML/CSS | 3.1.6 | Dashboard dark mode |
| Gráficos | Chart.js (CDN) | 4.5.1 | Histórico de preços |
| Calendário | Flatpickr (CDN) | - | Date picker nos formulários |
| Fonte | Inter (Google Fonts) | - | Tipografia moderna |
| Scheduler | APScheduler | 3.11.2 | Polling automático a cada 24h |
| API de voos | SerpAPI (Google Flights) | 2.4.2 | Busca preços e disponibilidade |
| Email | Gmail SMTP (smtplib) | stdlib | Alertas por email |
| Validação | Pydantic + pydantic-settings | 2.11.1 | Schemas e configuração |
| Testes | Pytest | 8.3.5 | 184 testes automatizados |
| HTTP client | HTTPX | 0.28.1 | Cliente HTTP para testes |

---

## Fluxo de Operação

```
1. Usuário cria um Grupo de Rota no dashboard
   (origens, destinos, datas, passageiros, paradas)
        |
        v
2. A cada 24h, o Scheduler dispara o polling
   (ou o usuário clica "Buscar agora")
        |
        v
3. O Polling Service gera combinações:
   origem x destino x datas (a cada 7 dias no período)
        |
        v
4. Pra cada combinação, chama a SerpAPI:
   1 chamada = voos + price insights (economiza 50%)
        |
        v
5. Salva FlightSnapshots no banco
   (preço, companhia, classificação LOW/MEDIUM/HIGH)
   Deduplicação: não salva o mesmo voo 2x no mesmo ciclo
        |
        v
6. Signal Service analisa os snapshots:
   - PRECO_ABAIXO_HISTORICO: preço atual < média dos últimos 14 snapshots
   - JANELA_OTIMA: falta 21-90 dias (doméstico) ou 30-120 (internacional)
   Deduplicação: mesmo sinal não repete em 12h
        |
        v
7. Se detectou sinal, envia 1 email consolidado por grupo
   (rota mais barata, top 3 datas, resumo, link de silenciar)
        |
        v
8. Dashboard mostra tudo: cards com preço, badge de sinal,
   botão "Ver voos" que abre o Google Flights
```

---

## Banco de Dados

Arquivo único: `flight_monitor.db` na raiz do projeto. Criado automaticamente ao iniciar o servidor.

### Tabela: route_groups
Grupos de monitoramento criados pelo usuário.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | INTEGER PK | Identificador |
| name | VARCHAR(100) | Nome do grupo (ex: "SP Setembro") |
| origins | JSON | Lista de códigos IATA de origem (ex: ["REC", "JPA"]) |
| destinations | JSON | Lista de códigos IATA de destino (ex: ["GRU", "CGH"]) |
| duration_days | INTEGER | Duração da viagem em dias |
| travel_start | DATE | Início do período de viagem |
| travel_end | DATE | Fim do período de viagem |
| target_price | FLOAT (null) | Preço-alvo opcional |
| passengers | INTEGER | Número de passageiros (padrão: 1) |
| max_stops | INTEGER (null) | null=qualquer, 0=direto, 1=até 1 conexão |
| is_active | BOOLEAN | Se o grupo está ativo para polling |
| silenced_until | DATETIME (null) | Até quando os alertas estão silenciados |
| created_at | DATETIME | Data de criação |
| updated_at | DATETIME | Última atualização |

### Tabela: flight_snapshots
Cada voo encontrado pelo polling.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | INTEGER PK | Identificador |
| route_group_id | INTEGER FK | Grupo que gerou este snapshot |
| origin | VARCHAR(3) | Código IATA de origem |
| destination | VARCHAR(3) | Código IATA de destino |
| departure_date | DATE | Data de ida |
| return_date | DATE | Data de volta |
| price | FLOAT | Preço em BRL (ida e volta, 1 passageiro) |
| currency | VARCHAR(3) | Moeda (sempre "BRL") |
| airline | VARCHAR(2) | Companhia aérea |
| price_min | FLOAT (null) | Menor preço do Google (price insights) |
| price_first_quartile | FLOAT (null) | Limite inferior da faixa típica |
| price_median | FLOAT (null) | Mediana da faixa típica |
| price_third_quartile | FLOAT (null) | Limite superior da faixa típica |
| price_max | FLOAT (null) | - |
| price_classification | VARCHAR(10) (null) | LOW, MEDIUM ou HIGH |
| collected_at | DATETIME | Timestamp da coleta |

### Tabela: detected_signals
Sinais de oportunidade detectados.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | INTEGER PK | Identificador |
| route_group_id | INTEGER FK | Grupo relacionado |
| flight_snapshot_id | INTEGER FK | Snapshot que gerou o sinal |
| origin | VARCHAR(3) | Origem |
| destination | VARCHAR(3) | Destino |
| departure_date | DATE | Data de ida |
| return_date | DATE | Data de volta |
| signal_type | VARCHAR(30) | PRECO_ABAIXO_HISTORICO ou JANELA_OTIMA |
| urgency | VARCHAR(10) | MEDIA |
| details | VARCHAR(500) | Detalhes do sinal |
| price_at_detection | FLOAT | Preço no momento da detecção |
| detected_at | DATETIME | Timestamp da detecção |

### Tabela: booking_class_snapshots (legado)
Herdada do Amadeus, não utilizada com SerpAPI. Mantida no schema.

---

## Estrutura de Arquivos

```
flight-monitor/
├── main.py                    # Ponto de entrada (FastAPI + scheduler)
├── .env                       # Credenciais (SerpAPI, Gmail)
├── flight_monitor.db          # Banco SQLite (auto-criado)
├── requirements.txt           # Dependências Python
├── DOCS.md                    # Este arquivo
│
├── app/
│   ├── config.py              # Carrega .env via pydantic-settings
│   ├── database.py            # Engine SQLAlchemy, SessionLocal, Base
│   ├── models.py              # 4 tabelas ORM
│   ├── schemas.py             # Validação Pydantic pra API REST
│   ├── scheduler.py           # APScheduler (polling 24h)
│   │
│   ├── routes/
│   │   ├── dashboard.py       # Páginas HTML (index, detail, create, edit, toggle, polling)
│   │   ├── route_groups.py    # API REST JSON (CRUD grupos)
│   │   └── alerts.py          # Silenciar alertas via HMAC token
│   │
│   ├── services/
│   │   ├── serpapi_client.py      # Wrapper SerpAPI (1 chamada = voos + insights)
│   │   ├── polling_service.py     # Orquestra polling: busca, salva, detecta, envia email
│   │   ├── snapshot_service.py    # Salva snapshots + deduplicação
│   │   ├── signal_service.py      # Detecta sinais (PRECO_ABAIXO_HISTORICO, JANELA_OTIMA)
│   │   ├── alert_service.py       # Email consolidado + HMAC token
│   │   ├── dashboard_service.py   # Queries de agregação pro dashboard
│   │   ├── airport_service.py     # Busca e valida aeroportos
│   │   └── route_group_service.py # Limite de 10 grupos ativos
│   │
│   ├── templates/             # HTML Jinja2 (dark mode)
│   │   ├── base.html          # Layout base (header, loading, flash)
│   │   ├── error.html         # Página de erro amigável
│   │   └── dashboard/
│   │       ├── index.html     # Página principal (summary, cards, badge)
│   │       ├── detail.html    # Gráfico Chart.js de histórico
│   │       ├── create.html    # Formulário criar grupo
│   │       └── edit.html      # Formulário editar grupo
│   │
│   └── data/
│       └── airports.json      # ~150 aeroportos (IATA, cidade, país)
│
└── tests/                     # 184 testes automatizados
    ├── conftest.py            # Fixtures (banco in-memory, client HTTP)
    └── test_*.py              # 18 arquivos de teste
```

---

## Configuração (.env)

```
DATABASE_URL=sqlite:///./flight_monitor.db
SERPAPI_API_KEY=sua_chave_aqui
GMAIL_SENDER=seu@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
GMAIL_RECIPIENT=seu@gmail.com
```

- **SERPAPI_API_KEY**: Obtida em https://serpapi.com (free tier: 250 buscas/mês)
- **GMAIL_APP_PASSWORD**: Gerada em Google > Segurança > Senhas de app (requer 2FA ativado)

---

## Como Rodar

```bash
cd "caminho/do/projeto/flight-monitor"
venv\Scripts\activate
python main.py
```

Acesse: http://localhost:8000

---

## Limites Atuais

- **SerpAPI free tier:** 250 buscas/mês (comporta ~2 grupos com polling 1x/dia)
- **Sinais ativos:** PRECO_ABAIXO_HISTORICO e JANELA_OTIMA
- **Banco local:** Sem migrations Alembic (deletar o .db recria do zero)
- **Servidor local:** Precisa estar rodando pra polling funcionar

---

## Histórico de Versões

| Versão | O que entregou |
|--------|---------------|
| v1.0 | Foundation, Data Collection, Signal Detection, Gmail Alerts, Web Dashboard |
| v1.1 | Email consolidado, datas BR, feedback UX, página de erro, fix duplicatas |
| v1.2 | Visual polish (dark mode, cards, tipografia, cores semânticas) |
| Extra | Autocomplete aeroportos, passageiros, paradas, Flatpickr, loading overlay, badge de atividade, link Google Flights |
