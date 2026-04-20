# Phase 30: Shareable Price Card (PNG) - Context

**Gathered:** 2026-04-20
**Status:** Implemented

<domain>
Card compartilhavel 1200x630 (padrao Open Graph) gerado via Pillow. Contem preco atual, rota, nome do grupo, contexto historico e branding. Usuario clica em "Compartilhar" no card do grupo, nova aba abre a imagem que ele pode salvar e postar no WhatsApp, IG, etc.
</domain>

<decisions>
- Dimensoes 1200x630: otimizado para Open Graph (WhatsApp, Twitter, Facebook)
- Gradient vertical escuro alinhado com identidade do produto
- Fontes: fallback hierarquico (arial.ttf -> DejaVuSans.ttf -> Helvetica.ttc -> default)
- Sem TTF custom bundled: reduz peso do repo, usa o que sistema oferecer
- Branding: "FLIGHT MONITOR" top-left, tag "PRECO JUSTO" top-right
- Ownership: rota valida user_id == group.user_id, retorna 404 caso contrario
- Cache-Control: public, max-age=900 (15 min) para reduzir geracao em visitas repetidas
</decisions>

<code_context>
### Arquivos novos
- app/services/share_card_service.py (build_price_card)
- tests/test_share_card.py (5 testes)

### Arquivos alterados
- requirements.txt: Pillow==11.2.1
- app/routes/dashboard.py: rota GET /groups/{id}/share-card.png
- app/templates/dashboard/index.html: botao "Compartilhar" no card
</code_context>

<specifics>
- Contexto historico opcional: se ctx presente, linha colorida acima do footer
- Contador de passageiros: inclui "total N pax: R$ X" quando pax > 1
</specifics>

<deferred>
- Fonte TTF bundled para consistencia visual cross-platform: futuro
- Preview no dashboard antes de abrir imagem: futuro
- Copy customizavel pelo usuario (ex: "Estou economizando com Flight Monitor"): futuro
</deferred>
