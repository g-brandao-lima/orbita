# flight-monitor

Sistema pessoal de monitoramento de passagens aéreas. Busca preços automaticamente, detecta oportunidades de compra e envia alertas por email.

## Estrutura

| Pasta | Descrição |
|---|---|
| `app/routes/` | Rotas do dashboard (HTML) e API REST |
| `app/services/` | Lógica de negócio: polling, sinais, email, aeroportos |
| `app/templates/` | Templates Jinja2 (dark mode) |
| `app/data/` | Base de aeroportos (150+ IATA codes) |
| `app/models.py` | Tabelas SQLAlchemy (RouteGroup, FlightSnapshot, DetectedSignal) |
| `app/scheduler.py` | APScheduler (polling automático 1x/dia) |
| `tests/` | 188 testes automatizados (Pytest) |

## Stack

- Python 3.13 + FastAPI + SQLAlchemy + SQLite
- SerpAPI (Google Flights) para busca de preços
- Jinja2 + Chart.js + Flatpickr para o dashboard
- Gmail SMTP para alertas por email
- APScheduler para polling automático

## Como usar

```bash
# Instalar
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Configurar (.env)
SERPAPI_API_KEY=sua_chave
GMAIL_SENDER=seu@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
GMAIL_RECIPIENT=seu@gmail.com

# Rodar
python main.py
# Acessar: http://localhost:8000
```

## O que faz

- **Grupos de Rota**: múltiplas origens/destinos, passageiros, paradas (direto/conexão), modo exploração
- **Polling**: busca preços via Google Flights 1x/dia (ou manual pelo dashboard)
- **Sinais**: detecta preço abaixo do histórico e janela ótima de compra
- **Email**: 1 email consolidado por grupo com rota mais barata e top 3 datas
- **Dashboard**: cards com preço, tendência, melhor dia da semana, sparkline, links Kayak/Skyscanner/Momondo
- **Autocomplete**: busca aeroporto por cidade ou código IATA

## Requisitos

- Python 3.10+
- Conta SerpAPI (grátis: 100 buscas/mês)
- Gmail com Senha de App (para alertas)
