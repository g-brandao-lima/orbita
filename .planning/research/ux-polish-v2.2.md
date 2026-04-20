# UX Polish v2.2: Especificação de Correções

Documento de design pronto para implementação. Mantém o design system existente: dark mode base `#0b0e14`, cards `#111827`, borda `#1e293b`, acento `#3b82f6`, tipografia Inter, fonte monospace para preços, raio 8 a 10 px, animações 150 a 200 ms.

## Correção 1: Toggle de modo de exibição de preço

### Problema

Hoje cada card mostra duas linhas sobrepostas: `por pessoa, ida e volta` e, quando `pax > 1`, `Total N passageiros: R$ X`. Isso polui o card e faz o usuário comparar dois números em vez de um. A preferência de leitura (por pessoa ou total) varia por objetivo: planejamento de orçamento familiar quer total, caça de oportunidade quer por pessoa.

### Proposta

Um único toggle global no `summary-strip`, à esquerda das ações, com dois estados mutuamente exclusivos. O modo selecionado se aplica a todos os cards simultaneamente. Persistência via cookie `price_mode` com valores `per_person` (default) ou `total`, `Max-Age=31536000`, `SameSite=Lax`, sem `HttpOnly` para permitir leitura no lado do servidor e também no cliente caso se opte por toggle sem reload.

Implementação pragmática v1: toggle aciona GET para `/?price_mode=total`, rota seta o cookie e redireciona para `/`. Sem JS adicional. v2 opcional pode usar fetch + re-render local.

Regra do grupo com 1 passageiro: o toggle permanece visível e ativo globalmente, mas a linha secundária `Total N passageiros` já não aparece (lógica atual). No modo `total` com `pax=1`, o preço exibido é o mesmo do modo `per_person`, e abaixo do preço aparece o sublabel `1 passageiro`, deixando claro que não há multiplicação. Esconder o toggle seletivamente por card seria inconsistente.

Sinalização do modo ativo: pill-group estilo segmented control, fundo `#1e293b`, o segmento ativo com fundo `#3b82f6` e texto branco, inativo com texto `#94a3b8`. Sublabel do card muda conforme o modo: `por pessoa, ida e volta` ou `total da viagem, N passageiros`.

### Mockup

```html
<div class="price-mode-toggle" role="group" aria-label="Modo de exibição de preço">
  <a href="?price_mode=per_person"
     class="pmt-opt {% if price_mode == 'per_person' %}active{% endif %}"
     aria-pressed="{{ 'true' if price_mode == 'per_person' else 'false' }}">
    Por pessoa
  </a>
  <a href="?price_mode=total"
     class="pmt-opt {% if price_mode == 'total' %}active{% endif %}"
     aria-pressed="{{ 'true' if price_mode == 'total' else 'false' }}">
    Total da viagem
  </a>
</div>

<style>
.price-mode-toggle {
  display: inline-flex; background: #1e293b; border-radius: 8px; padding: 2px;
  border: 1px solid #334155;
}
.pmt-opt {
  padding: 5px 12px; font-size: 12px; font-weight: 600; color: #94a3b8;
  border-radius: 6px; text-decoration: none; transition: all 0.15s ease;
  line-height: 1.4;
}
.pmt-opt:hover { color: #e2e8f0; }
.pmt-opt.active { background: #3b82f6; color: #fff; }
.pmt-opt:focus-visible { outline: 2px solid #60a5fa; outline-offset: 2px; }
</style>
```

### Copy

- Rótulos: `Por pessoa`, `Total da viagem`
- Sublabel no card, modo per_person: `por pessoa, ida e volta`
- Sublabel no card, modo total com pax>1: `total, {{pax}} passageiros`
- Sublabel no card, modo total com pax=1: `1 passageiro, ida e volta`

### Observações

Acessibilidade: `role="group"` + `aria-pressed` comunica ao leitor de tela qual opção está ativa. Tab navega entre os dois segmentos. Contraste do segmento ativo atende AA (branco sobre `#3b82f6`, 4.7:1).

## Correção 2: Decolar, Google Flights, Skyscanner

### Problema

Trio atual (Kayak, Skyscanner, Momondo) é genérico e de baixa conversão para o mercado brasileiro. Decolar é a OTA dominante no Brasil, Google Flights é o que mais gera confiança pós-pesquisa, Skyscanner cobre o caso de viagem internacional e metabusca. Além disso, o preço do card vem do Google Flights, então incluí-lo nos botões evita a sensação de que os destinos são concorrentes do dado mostrado.

### Proposta

Trio fixo nessa ordem: **Google Flights**, **Decolar**, **Skyscanner**. Ordem justificada: Google Flights primeiro porque é a fonte do preço (clique confirma o valor visto), Decolar segundo porque é onde o brasileiro fecha, Skyscanner terceiro como alternativa de preço agregado.

Cada botão ganha um micro-ícone de 12 px à esquerda (favicon-style) e o nome abreviado. Cor base neutra idêntica aos botões de ação atuais (borda `#1e293b`, texto `#64748b`), sem branding colorido no estado idle para preservar a hierarquia visual. No hover, borda muda para a cor da marca como reforço sutil:

- Google Flights hover: borda `#4285F4`, texto `#e2e8f0`
- Decolar hover: borda `#552f91`, texto `#e2e8f0`
- Skyscanner hover: borda `#0770e3`, texto `#e2e8f0`

Para deixar claro que o preço vem do Google Flights sem poluir o card, o badge de fonte (Correção 4) faz o trabalho. Opcionalmente, o primeiro botão pode carregar um pequeno indicador `·` com tooltip `Mesma fonte do preço`.

### Deep links

Os endpoints reais devem ser encapsulados em `app/services/booking_urls.py`. Formato esperado para cada um:

```python
def booking_urls(origin, destination, dep_date, ret_date, pax):
    # dep_date/ret_date formato YYYY-MM-DD
    return {
        "google_flights": (
            f"https://www.google.com/travel/flights?q=Flights%20to%20{destination}%20"
            f"from%20{origin}%20on%20{dep_date}%20through%20{ret_date}%20for%20{pax}%20adults"
        ),
        "decolar": (
            f"https://www.decolar.com/shop/flights/results/roundtrip/"
            f"{origin}/{destination}/{dep_date}/{ret_date}/{pax}/0/0"
        ),
        "skyscanner": (
            f"https://www.skyscanner.com.br/transport/flights/"
            f"{origin.lower()}/{destination.lower()}/"
            f"{dep_date[2:4]}{dep_date[5:7]}{dep_date[8:10]}/"
            f"{ret_date[2:4]}{ret_date[5:7]}{ret_date[8:10]}/"
            f"?adults={pax}"
        ),
    }
```

### Mockup

```html
<div class="card-actions">
  <a href="{{ urls.google_flights }}" target="_blank" rel="noopener"
     class="booking-link" data-brand="google">
    <span class="booking-ico">G</span> Google Flights
  </a>
  <a href="{{ urls.decolar }}" target="_blank" rel="noopener"
     class="booking-link" data-brand="decolar">
    <span class="booking-ico">D</span> Decolar
  </a>
  <a href="{{ urls.skyscanner }}" target="_blank" rel="noopener"
     class="booking-link" data-brand="skyscanner">
    <span class="booking-ico">S</span> Skyscanner
  </a>
</div>

<style>
.booking-link {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 4px 10px; border: 1px solid #1e293b; border-radius: 6px;
  font-size: 12px; color: #64748b; text-decoration: none; min-height: 28px;
  transition: border-color 0.15s, color 0.15s;
}
.booking-ico {
  width: 14px; height: 14px; border-radius: 3px; font-size: 9px; font-weight: 700;
  display: inline-flex; align-items: center; justify-content: center;
  background: #1e293b; color: #94a3b8;
}
.booking-link[data-brand="google"]:hover { border-color: #4285F4; color: #e2e8f0; }
.booking-link[data-brand="decolar"]:hover { border-color: #a855f7; color: #e2e8f0; }
.booking-link[data-brand="skyscanner"]:hover { border-color: #0770e3; color: #e2e8f0; }
</style>
```

### Observações

`rel="noopener"` já está correto. Adicionar `aria-label` explícito no formato `Abrir busca no Google Flights em nova aba`. Validar deep links em mobile, a Decolar redireciona rotas antigas. Em viagens internacionais, o Skyscanner brasileiro pode não cobrir rotas raras, mas o link degrada para página de resultado genérica, aceitável.

## Correção 3: Painel /admin/stats com dados operacionais

### Problema

A métrica `Buscas restantes: X/250` no summary-strip é técnica, irrelevante para uso normal e vaza informação sobre a conta SerpAPI do dono para qualquer visitante autenticado. Ruído visual e leve vazamento.

### Proposta

Remover o `metric` de buscas restantes do `summary-strip`. Criar rota `/admin/stats` renderizada somente se `user.email == "gustavob096@gmail.com"`. Qualquer outro email recebe 404 (não 403, para não confirmar a existência da rota).

Descoberta da rota pelo dono: ícone de engrenagem discreto no header, à direita do nome, visível apenas quando o email bate. Não colocar no footer (invisível) nem em banner (desnecessário).

Conteúdo do painel, quatro blocos em grid 2x2 em desktop, empilhados em mobile:

1. **Quota SerpAPI**: número grande com uso do mês (`47 de 250`), barra de progresso, data de reset e consumo projetado pro fim do mês baseado no ritmo atual.
2. **Distribuição de fonte, últimos 30 polls**: lista horizontal com três barras proporcionais (`serpapi 78%`, `fast_flights 18%`, `kiwi 4%`), cores do sistema (`#3b82f6`, `#a855f7`, `#10b981`). Simples, sem biblioteca de gráfico extra.
3. **Cache hit rate**: percentual grande, tendência vs. semana anterior, número absoluto de hits e misses.
4. **Últimos erros**: tabela compacta com timestamp, fonte, código ou mensagem truncada, máximo 10 linhas.

### Mockup

```html
<!-- Header, só renderiza se admin -->
{% if is_admin %}
<a href="/admin/stats" class="btn btn-ghost btn-sm" title="Admin" aria-label="Painel admin">
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
       stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="12" cy="12" r="3"/>
    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
  </svg>
</a>
{% endif %}

<!-- /admin/stats -->
<div class="admin-grid">
  <section class="admin-block">
    <h3 class="admin-title">Quota SerpAPI</h3>
    <div class="admin-big">47<span class="admin-denom">/250</span></div>
    <div class="admin-bar"><div class="admin-bar-fill" style="width:18.8%"></div></div>
    <div class="admin-sub">Reset em 12 dias · projeção 118 no fim do mês</div>
  </section>
  <section class="admin-block">
    <h3 class="admin-title">Fontes, últimos 30 polls</h3>
    <div class="source-bar">
      <span style="flex:0.78;background:#3b82f6">Google Flights 78%</span>
      <span style="flex:0.18;background:#a855f7">fast_flights 18%</span>
      <span style="flex:0.04;background:#10b981">Kiwi 4%</span>
    </div>
  </section>
  <!-- ... -->
</div>
```

### Copy

- Rótulos: `Quota SerpAPI`, `Fontes, últimos 30 polls`, `Cache hit rate`, `Últimos erros`.
- Estado vazio de erros: `Nenhum erro nas últimas 24h`.
- Link do header: tooltip `Painel admin`, sem texto visível.

### Observações

404 em vez de 403 evita enumeração. A checagem deve acontecer tanto na rota (FastAPI dependency) quanto no template (evitar vazamento em cache de HTML). Não logar acessos negados com detalhe, apenas contador agregado.

## Correção 4: Badge de fonte unificado

### Problema

Hoje existem duas cores e dois labels: `Google Flights` em azul (`serpapi`) e `Google Flights (scraping)` em violeta (`fast_flights`). Ambos são, para o usuário, o mesmo dado: preço do Google Flights. A palavra `scraping` é ruído técnico e soa pouco confiável.

### Proposta

Unificar visualmente. Qualquer fonte cujo dado original venha do Google Flights mostra um badge único: `Google Flights`, cor azul (`#1e3a5f` fundo, `#93c5fd` texto, borda `#1e40af`). Kiwi mantém sua cor distinta porque é outra fonte.

Tooltip nativo via `title` no hover, texto: `Dados agregados do Google Flights`. Sem popover customizado, economiza JS.

Para manter rastreabilidade operacional (qual fonte interna foi usada), essa info fica apenas no painel /admin/stats. O usuário não precisa saber se veio de SerpAPI ou fast-flights, apenas que a origem do dado é o Google Flights.

### Mockup

```html
<span class="source-badge source-google"
      title="Dados agregados do Google Flights">
  Google Flights
</span>

<style>
.source-badge {
  display: inline-block; font-size: 10px; padding: 2px 6px; border-radius: 4px;
  letter-spacing: 0.3px; text-transform: uppercase; cursor: help;
}
.source-google { background: #1e3a5f; border: 1px solid #1e40af; color: #93c5fd; }
.source-kiwi   { background: #5b21b6; border: 1px solid #7c3aed; color: #c4b5fd; }
</style>
```

Lógica Jinja:

```jinja
{% set google_sources = ['serpapi', 'fast_flights'] %}
<span class="source-badge source-{{ 'google' if snap.source in google_sources else snap.source }}"
      title="{% if snap.source in google_sources %}Dados agregados do Google Flights{% else %}Fonte: {{ snap.source }}{% endif %}">
  {% if snap.source in google_sources %}Google Flights{% else %}{{ snap.source|capitalize }}{% endif %}
</span>
```

### Observações

`cursor: help` dá affordance de tooltip. Para leitores de tela, `title` já é lido. Contraste `#93c5fd` sobre `#1e3a5f` atinge 7.1:1, AAA. Remover classes `.source-serpapi` e `.source-fast_flights` do CSS após migração.

## Ordem de implementação recomendada

1. **Correção 4 (badge unificado)**: menor risco, 1 arquivo de template e 1 bloco CSS, zero dependência de rota ou auth. Entrega percebível imediata. Primeiro porque destrava mental model correto antes das demais.
2. **Correção 3 (remover métrica e criar /admin/stats)**: risco médio porque envolve nova rota e gating por email, mas remove ruído antes de adicionar toggle. Fazer antes da Correção 1 evita reorganizar o summary-strip duas vezes.
3. **Correção 1 (toggle de preço)**: maior impacto em UX diária. Introduz cookie e altera todos os cards, requer teste manual com grupos de 1 e de múltiplos passageiros.
4. **Correção 2 (botões de compra)**: por último porque exige testar deep links reais em três OTAs, risco de ajuste fino. Isolado no card-bottom, não bloqueia as demais.
