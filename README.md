# Flight Monitor

Sistema pessoal de monitoramento de passagens aéreas que busca preços automaticamente, detecta oportunidades de compra e envia alertas por email. Dashboard dark mode com visualização de preços, tendências e links diretos para compra.

![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow)

## O que faz

- Monitora preços de voos automaticamente (1x por dia via SerpAPI/Google Flights)
- Detecta sinais de oportunidade (preço abaixo do histórico, janela ideal de compra)
- Envia 1 email consolidado por grupo com a rota mais barata e as melhores datas
- Dashboard dark mode com cards, tendências de preço e links diretos para Kayak/Skyscanner/Momondo
- Suporta múltiplas origens, destinos, passageiros e filtro de paradas (direto/conexão)
- Modo Exploração para descobrir o mês mais barato em um período de até 12 meses

## Stack

| Tecnologia | Versão | Uso |
|-----------|--------|-----|
| Python | 3.13 | Backend |
| FastAPI | 0.115 | API e servidor web |
| SQLAlchemy | 2.0 | ORM e banco de dados |
| SQLite | - | Armazenamento local |
| Jinja2 | 3.1 | Templates HTML |
| APScheduler | 3.11 | Polling automático |
| SerpAPI | - | Busca de preços (Google Flights) |
| Chart.js | 4.5 | Gráficos de histórico |
| Flatpickr | - | Date picker |
| Inter | - | Tipografia (Google Fonts) |
| Pytest | 8.3 | Testes automatizados (188 testes) |

## Como rodar

### Pré-requisitos

- Python 3.10+
- Conta SerpAPI (grátis: https://serpapi.com)
- Conta Gmail com Senha de App (para alertas por email)

### Instalação

```bash
# Clonar repositório
git clone https://github.com/g-brandao-lima/flight-monitor.git
cd flight-monitor

# Criar ambiente virtual
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Instalar dependências
pip install -r requirements.txt
```

### Configuração

Criar arquivo `.env` na raiz:

```env
DATABASE_URL=sqlite:///./flight_monitor.db
SERPAPI_API_KEY=sua_chave_aqui
GMAIL_SENDER=seu@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
GMAIL_RECIPIENT=seu@gmail.com
```

### Executar

```bash
python main.py
```

Acessar: http://localhost:8000

## Funcionalidades

### Dashboard
- Cards com preço em destaque, companhia aérea, datas e badge de sinal
- Tendência de preço (subindo/descendo vs última coleta)
- Melhor dia da semana para voar (baseado no histórico)
- Sparkline de preço dos últimos dias
- Links diretos para Kayak, Skyscanner e Momondo
- Busca manual de preços com barra de progresso animada
- Activity feed com últimos sinais e coletas

### Grupos de Rota
- Múltiplas origens e destinos por grupo
- Autocomplete de aeroportos (150+ aeroportos com busca por cidade)
- Modo Normal (datas específicas) ou Exploração (descobre o mês mais barato)
- Filtro de paradas (qualquer, direto, até 1 conexão)
- Número de passageiros (preço multiplicado automaticamente)

### Alertas
- Email consolidado por grupo (não por sinal individual)
- Rota mais barata + top 3 melhores datas + resumo
- Link de silenciar alertas por 24h via HMAC token
- Formato de data brasileiro (dd/mm/aaaa)

### Sinais Detectados
- **Preço Abaixo do Histórico**: preço atual abaixo da média dos últimos 14 snapshots
- **Janela Ótima**: faltam 21-90 dias (doméstico) ou 30-120 dias (internacional)
- Deduplicação: mesmo sinal não repete em 12 horas

## Estrutura do Projeto

```
flight-monitor/
├── main.py                    # Ponto de entrada
├── .env                       # Credenciais (não versionado)
├── requirements.txt           # Dependências
├── app/
│   ├── config.py              # Configuração via pydantic-settings
│   ├── database.py            # SQLAlchemy engine
│   ├── models.py              # 4 tabelas ORM
│   ├── schemas.py             # Validação Pydantic
│   ├── scheduler.py           # APScheduler (24h)
│   ├── routes/
│   │   ├── dashboard.py       # Páginas HTML
│   │   ├── route_groups.py    # API REST
│   │   └── alerts.py          # Silenciar alertas
│   ├── services/
│   │   ├── serpapi_client.py   # Wrapper SerpAPI
│   │   ├── polling_service.py  # Orquestrador de coleta
│   │   ├── signal_service.py   # Detecção de sinais
│   │   ├── alert_service.py    # Email consolidado
│   │   ├── dashboard_service.py # Queries de agregação
│   │   ├── airport_service.py  # Busca de aeroportos
│   │   └── snapshot_service.py # Persistência + dedup
│   ├── templates/             # Jinja2 (dark mode)
│   └── data/
│       └── airports.json      # 150+ aeroportos
└── tests/                     # 188 testes automatizados
```

## Limites

- **SerpAPI free tier**: 100 buscas/mês (comporta ~2 grupos com polling 1x/dia)
- **Banco local**: SQLite sem migrations (deletar .db recria do zero)
- **Servidor local**: precisa estar rodando para o polling funcionar

## Histórico de Versões

| Versão | Entrega |
|--------|---------|
| v1.0 | Foundation, Data Collection, Signal Detection, Gmail Alerts, Web Dashboard |
| v1.1 | Email consolidado, datas BR, feedback UX, página de erro, fix duplicatas |
| v1.2 | Dark mode, tipografia Inter, cards redesenhados, deep links, modo exploração |

## Autor

**Gustavo Brandão** - [@g-brandao-lima](https://github.com/g-brandao-lima)
