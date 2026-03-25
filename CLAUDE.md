<!-- GSD:project-start source:PROJECT.md -->
## Project

**Flight Monitor**

Sistema pessoal de monitoramento de passagens aéreas que rastreia a velocidade de fechamento dos baldes de inventário (booking classes) de voos para prever o momento ideal de compra ANTES que o preço suba — não depois. Para uso próprio, rodando localmente com deploy futuro no Fly.io.

**Core Value:** Detectar o momento certo de comprar uma passagem antes que o preço suba, usando dados de inventário reais (booking classes via Amadeus API) que nenhum sistema consumer expõe ao usuário.

### Constraints

- **API**: Amadeus Self-Service free tier — 2.000 calls/mês; máximo ~4 grupos ativos com 2 pollings/dia
- **Stack**: Python, FastAPI, SQLite, APScheduler, Telegram Bot API — sem JavaScript framework no frontend
- **Infra**: Local first → Fly.io free tier; sem VPS pago nesta versão
- **Usuários**: Single-user, sem autenticação complexa
- **Scope**: Roundtrip only; voos GDS (não LCC direto)
<!-- GSD:project-end -->

<!-- GSD:stack-start source:STACK.md -->
## Technology Stack

Technology stack not yet documented. Will populate after codebase mapping or first phase.
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd:quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd:debug` for investigation and bug fixing
- `/gsd:execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd:profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
