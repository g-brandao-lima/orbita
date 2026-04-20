# Phase 28: Empty State com Rotas Populares - Context

**Gathered:** 2026-04-20
**Status:** Implemented

<domain>
Primeiro login nunca mostra dashboard vazio: sugere 6 rotas populares brasileiras como ponto de partida. Clique unico cria o grupo com datas sugeridas automaticamente.
</domain>

<decisions>
- 6 rotas hardcoded (GRU-LIS, GRU-MIA, GRU-EZE, GIG-CDG, REC-LIS, GRU-SCL)
- Datas default: partida daqui a 60 dias, janela de 60 dias
- Passageiros default: 1
- Clique em "Monitorar esta rota" cria grupo e redireciona para edicao (usuario pode ajustar datas)
- Lista em `app/services/popular_routes.py` facil de expandir
</decisions>

<code_context>
### Arquivos novos
- app/services/popular_routes.py
- tests/test_popular_routes.py (5 testes)

### Arquivos alterados
- app/routes/dashboard.py: rota /groups/create-from-template + context
- app/templates/dashboard/index.html: novo empty state com grid de rotas
</code_context>

<specifics>
- Datas calculadas no momento do POST (sempre relativas a hoje)
- Rate limit LIMIT_WRITE aplicado
- Redireciona para /edit apos criar (usuario ve dados e pode ajustar)
</specifics>

<deferred>
- Adicionar imagem do destino em cada card: futuro
- Sparkline historico publico nos cards de rotas populares: Phase 32 (indice publico)
- Mais rotas: quando validar engagement real
</deferred>
