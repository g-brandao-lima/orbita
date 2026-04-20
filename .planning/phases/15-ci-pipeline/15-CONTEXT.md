# Phase 15: CI Pipeline - Context

**Gathered:** 2026-04-20
**Status:** Implemented
**Mode:** Auto-generated (autonomous night run)

<domain>
## Phase Boundary

Adicionar workflow GitHub Actions que executa pytest em todo push/PR para master, bloqueando deploy quando testes falham. Nao inclui coverage reports (seria over-engineering para 200 usuarios) nem lint/format (fica como follow-up).

</domain>

<decisions>
## Implementation Decisions

- Workflow: `.github/workflows/ci.yml`
- Python 3.11 (matching runtime.txt e Render)
- Cache pip via actions/setup-python@v5
- Env vars de teste hardcoded no workflow (sao mocks, nao secrets)
- Ignora tests/test_amadeus_client.py (legado, sera removido em Phase 21)
- Timeout de 10 minutos (suite atual roda em ~15s)
- Roda em push e PR para master ou main

</decisions>

<code_context>
## Existing Code Insights

### Integration Points
- runtime.txt: python-3.11.12 (workflow usa 3.11)
- requirements.txt: dependencies existentes cobrem testes
- pyproject.toml: testpaths e python_files ja configurados

</code_context>

<specifics>
## Specific Ideas

- Render auto-deploy continua ativo, mas como precisa de merge para master e CI roda antes, efetivamente bloqueia deploy com teste vermelho.

</specifics>

<deferred>
## Deferred Ideas

- Coverage reporting (follow-up apos 1k+ usuarios)
- Ruff/Black em PR (follow-up)
- Pre-commit hooks locais (opcional pelo dev)

</deferred>
