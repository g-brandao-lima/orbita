# Refinamento: Viagens Multi-Trecho no Flight Monitor

Documento de refinamento de produto para suportar viagens com mais de um trecho (multi-city, open jaw, stopover). Escrito em linguagem de PO, com foco em decisoes objetivas, MVP enxuto e backlog executavel.

Exemplo de referencia do usuario: Recife para Sao Paulo em 01/09, cinco dias em SP, Sao Paulo para Gramado em 06/09, tres dias em POA, Gramado para Recife em 09/09. Tres trechos, datas fixas, duracoes de estadia variaveis, origem final igual a origem inicial mas passando por cidade intermediaria que nao e a origem.

## 1. Mapa de casos de uso reais

**Caso A: Stopover intencional (circular com retorno a casa)**
RE para SP (5 dias), SP para POA (3 dias), POA para RE. E o caso descrito pelo usuario. Caracteristica: ida-meio-volta, origem inicial coincide com destino final. Tres trechos, sempre aereo, datas fixas ou com flexibilidade pequena.

**Caso B: Volta por cidade diferente (open jaw classico)**
RE para SP (ida), SP para BSB (trecho intermediario terrestre ou aereo), BSB para RE. Uma das pernas pode nao ser aereo, o que o Flight Monitor nao monitora. Se todas sao aereas, e identico ao Caso A.

**Caso C: Viagem circular com multiplos destinos**
RE para SP, SP para POA, POA para FLN, FLN para RE. Quatro trechos ou mais, estilo mochilao.

**Caso D: Open jaw sem retorno a origem**
RE para SP (ida), MIA para RE (volta de outro destino, usuario se deslocou por terra entre SP e MIA). Raro em voos domesticos, comum em roteiros internacionais longos.

**Priorizacao para MVP**: implementar apenas o **Caso A** (stopover circular com datas fixas). Justificativa: cobre a demanda real declarada, e o padrao mais frequente em viagens domesticas brasileiras com escala planejada, e nao exige re-arquitetar a nocao de "viagem" para lidar com trechos terrestres. Casos B, C e D sao generalizacoes naturais do modelo do Caso A e entram em fases posteriores, nao na primeira entrega. Viagem circular de 4+ trechos (Caso C) e extensao direta do Caso A sem mudanca de modelo, apenas limite numerico.

## 2. Regras de negocio

**Quantidade de trechos**
Minimo 2 (equivalente a um round-trip expresso como ida + volta). Maximo 5 no MVP. Justificativa: cada trecho adiciona N chamadas a API por ciclo de polling; acima de 5 o custo de quota cresce demais para um grupo unico (ver secao 5). Configuravel por feature flag caso o usuario queira ampliar.

**Datas de cada trecho**
MVP: datas fixas. O usuario declara a data exata de cada partida. Flexibilidade vem como fase posterior via campo `flex_days` por trecho (+/- N dias). Motivo: introduzir flexibilidade por trecho multiplica combinacoes (5 trechos com +/-3 dias cada = 7^5 = 16k combinacoes) e estoura quota imediatamente.

**Duracao de estadia**
Implicita na sequencia de datas. Se o trecho 1 chega em 01/09 e o trecho 2 parte em 06/09, estadia sao 5 dias. Nao precisa campo separado. Na UI isso pode ser exibido como "X dias em SP" calculado.

**O que monitorar**
Preco total da viagem (soma dos trechos) e preco de cada trecho individualmente. Classificacao de preco (baixo/medio/alto) e feita por trecho, usando faixa historica daquela rota especifica. Alerta de "preco total bom" usa a soma comparada a media historica do grupo multi-trecho. MVP: calcular e exibir soma; classificacao de banda total e fase posterior (precisa de historico suficiente).

**Classificacao de alerta quando multiplos trechos se movem**
Regra: emitir um unico alerta consolidado por viagem por ciclo de polling. Se multiplos trechos tem movimento relevante, agregar todos no mesmo email, igual ao `compose_consolidated_email` atual faz para um grupo. Urgencia do alerta consolidado e a maior urgencia entre os trechos. Nao emitir alertas separados por trecho.

**Trecho sem voo disponivel**
Registrar snapshot de "sem voo" com preco nulo e marcar flag `no_availability`. Nao bloquear o processamento dos outros trechos. No email consolidado, destacar o trecho problematico. Importante para o usuario saber que precisa rever a data ou o trecho, nao so "fiquei sem alerta".

**Compra conjunta vs separada**
Decisao de produto: monitorar cada trecho como **compra separada** (passagens individuais). Justificativa: voos multi-city vendidos como bilhete unico (via SerpAPI multi-city mode) costumam ser mais caros que a soma de tres passagens one-way compradas separadamente no mercado brasileiro. Confirmar com o usuario. Bilhete unico multi-city e fase posterior se houver demanda.

## 3. Modelo de dados proposto

**Nova tabela `Trip`** (substitui semantica de viagem que hoje esta implicita em RouteGroup)

```
Trip
- id
- user_id
- name
- passengers
- max_stops
- mode (normal / exploracao)
- is_active
- silenced_until
- target_total_price (opcional, preco alvo da viagem inteira)
- created_at, updated_at
```

**Nova tabela `TripLeg`**

```
TripLeg
- id
- trip_id (FK)
- leg_order (1, 2, 3...)
- origin (IATA, 3 chars)
- destination (IATA)
- departure_date (date fixa no MVP)
- flex_days (int, default 0, reservado para fase posterior)
- target_leg_price (opcional)
```

**Snapshot e sinal**: adicionar `trip_leg_id` (FK) em `FlightSnapshot` e `DetectedSignal`. Manter `route_group_id` por compatibilidade durante transicao.

**Migracao de dados existentes**: cada `RouteGroup` atual vira um `Trip` com dois `TripLeg` (ida e volta). A expansao de multiplas origens/destinos do modelo antigo (permutacoes) vira **multiplos Trips**, nao um Trip com permutacoes. Isso simplifica semantica: uma viagem = uma sequencia fixa de trechos. Usuario que tinha grupo "RE-SP ou RE-GRU" fica com dois Trips separados apos migracao.

**Indices esperados**
- `trip_id` em TripLeg e Snapshot para query de consolidacao
- `leg_order` para ordenar trechos no dashboard e email
- Manter `ix_signal_dedup` estendido com `trip_leg_id`

**Compatibilidade com servicos atuais**
- `snapshot_service`: passa a aceitar `trip_leg_id` opcional; durante transicao, manter `route_group_id` dual.
- `polling_service`: loop externo troca de "grupos ativos" para "trips ativos"; dentro do trip, loop sobre `legs` em ordem. Ver secao 5.
- `alert_service.compose_consolidated_email`: passa a receber `Trip` e lista de snapshots/sinais agrupados por leg. Renderiza secoes por trecho na mesma mensagem.

## 4. Fluxo de UI

**Criacao de viagem**
Formulario unico com lista dinamica de trechos. O usuario preenche cabecalho (nome, passageiros, max_stops, mode) e adiciona trechos via botao "Adicionar trecho". Cada trecho tem origem, destino e data. Ao adicionar o trecho N+1, preencher origem automaticamente com o destino do trecho N (reduz digitacao, casos circulares). Minimo 2 trechos, maximo 5.

Wizard passo a passo e excessivo para single-user com menos de 5 etapas. Form dinamico unico e mais rapido e tem menor custo de manutencao.

**Validacoes de front**
- Data do trecho N+1 deve ser >= data do trecho N (estadia zero e permitida, ex: conexao no mesmo dia em roteiro)
- Origem do trecho N+1 deve ser igual ao destino do trecho N (viagem continua) ou aceitar "gap" explicito com warning (para Caso D futuro)
- Nao permitir origem == destino no mesmo trecho
- IATA valido (3 letras maiusculas, lista de aeroportos)

**Dashboard**
Cards de viagem listam nome e trechos em linha compacta: `REC 01/09 GRU 06/09 POA 09/09 REC`. Preco total atual visivel e preco por trecho em expansao (accordion). Badge de urgencia agregada. Viagens de 1 trecho (round-trip puro) continuam com layout atual; multi-trecho usa variacao do template.

**Email de alerta**
Um unico email por viagem por ciclo. Assunto: `[URGENCIA] TripName (3 trechos)`. Corpo: secao "Resumo" com total e variacao; secao por trecho com preco, airline, classificacao e link de busca. Manter botao de silenciamento no final. Reusa infraestrutura atual de `compose_consolidated_email`.

## 5. Impacto em polling e quota

**Chamadas por ciclo**
Hoje: grupo round-trip gera `N_origins * N_destinations * N_date_pairs` chamadas. Tipicamente 1 a 3.
Multi-trecho: cada trecho gera `N_date_pairs_desse_trecho` chamadas. Com datas fixas, cada trecho = 1 chamada por ciclo. Uma viagem de 5 trechos com datas fixas = 5 chamadas por ciclo.

**Quota Amadeus (2000/mes segundo CLAUDE.md do projeto) ou SerpAPI (250/mes)**
Com 2 pollings/dia = 60 ciclos/mes. Um Trip de 5 trechos consome 300 chamadas/mes. Limite pratico: 4 a 6 trips ativos simultaneamente dependendo do tamanho medio. Estabelecer teto de **10 trechos totais somados entre todos os Trips ativos do usuario**; bloquear ativacao alem disso com mensagem clara.

**Batch vs sequencial**
SerpAPI e fast-flights nao suportam batching nativo de rotas diferentes. Manter sequencial. Pode-se paralelizar com asyncio no futuro, mas nao e MVP. Priorizar retries e circuit breaker em falha de trecho individual (ja existe via try/except no polling atual).

**Suporte multi-city nativo das fontes**
SerpAPI google_flights suporta `type=3` (multi-city). Retorna preco unico do bilhete combinado. fast-flights nao suporta multi-city de forma estavel. Decisao de produto: MVP ignora multi-city nativo; trata cada trecho como busca one-way independente. Isso e consistente com a regra de negocio de "compra separada" (secao 2) e evita fragilidade de scraping.

**Tipo de busca por trecho**: one-way (nao round-trip). Requer ajuste em `search_flights` para aceitar `trip_type='one_way'` e nao exigir `return_date`. Hoje o servico assume round-trip.

## 6. Backlog estruturado

**Fase A: Modelo de dados + migracao**
Goal: introduzir Trip e TripLeg sem quebrar funcionalidade existente.
Requirements: criar tabelas via Alembic; script de migracao que converte cada RouteGroup em Trip + 2 TripLegs (ida/volta); adicionar `trip_leg_id` nullable em Snapshot e DetectedSignal; preservar dados historicos.
Sucesso: `alembic upgrade head` roda sem erro; todos os grupos existentes viram Trips; testes de migracao idempotente; polling continua funcionando via compatibilidade.
Dependencias: nenhuma.

**Fase B: Busca one-way e CRUD de Trip via API**
Goal: expor endpoints REST para criar, listar, editar e desativar Trips; adaptar `search_flights` para one-way.
Requirements: endpoints `POST/GET/PATCH/DELETE /api/v1/trips`; validacao de sequencia de legs; flight_search aceita `trip_type='one_way'` sem return_date.
Sucesso: criar Trip de 3 legs via curl, listar, editar, desativar; testes de API e de search one-way.
Dependencias: Fase A.

**Fase C: UI de criacao multi-trecho**
Goal: tela de criacao com form dinamico de legs.
Requirements: novo template HTML com JS vanilla para add/remove legs; auto-fill de origem; validacoes client-side; POST para endpoint da Fase B.
Sucesso: criar viagem REC-GRU-POA-REC pela UI em menos de 1 minuto.
Dependencias: Fase B.

**Fase D: Dashboard multi-trecho**
Goal: exibir Trips no dashboard com layout adaptado.
Requirements: card multi-trecho com sequencia de IATAs; preco total atual; accordion por trecho; badge de urgencia agregada.
Sucesso: dashboard renderiza 1 trip single-leg (migrado) e 1 trip 3-legs corretamente.
Dependencias: Fase B.

**Fase E: Polling e email consolidado para multi-trecho**
Goal: polling_service itera legs; alert_service renderiza email com secoes por trecho.
Requirements: `_poll_group` substituido por `_poll_trip` que itera legs; snapshots persistidos com `trip_leg_id`; detector de sinais agrupa por trip; email consolidado com secao por leg e total.
Sucesso: ciclo de polling gera 1 email com 3 secoes para trip de 3 legs; sinais deduplicados corretamente.
Dependencias: Fase A, B.

**Fase F: Guardas de quota e limites**
Goal: bloquear criacao/ativacao de Trip que estoure teto de trechos ativos.
Requirements: validacao no endpoint de ativacao; mensagem clara com contagem atual; dashboard mostra consumo de quota prevista.
Sucesso: tentar ativar 11o trecho bloqueia com 400 e mensagem explicativa.
Dependencias: Fase E.

**Fases posteriores (pos-MVP)**: flex_days por leg, preco alvo total, multi-city nativo via SerpAPI type=3, Caso B/D (legs terrestres e open jaw), historico de preco total da viagem e classificacao de banda.

## 7. Riscos e perguntas em aberto

**Nao-validavel sem uso real**
Se o preco total da viagem (soma) e metrica util para decisao, ou se o usuario decide por trecho. Validar com 2 a 3 viagens reais monitoradas antes de investir em classificacao de banda total.

Se o padrao "email consolidado por trip" e claro quando ha muitos trechos, ou se fica poluido. Testar com trip de 5 legs e iterar no template.

Se o teto de 5 legs por trip e 10 legs totais e adequado. Pode ser folgado ou apertado demais dependendo do perfil de uso.

**MVP mais enxuto**
Fases A + B + E entregam valor sem UI. Usuario cria trip via curl ou script, polling roda, email chega consolidado. A UI (Fase C, D) e necessaria para uso continuado mas nao para validar a hipotese central. Se tempo apertar, comecar sem UI e usar o script `poll.py` existente para rodar ciclos manuais.

**Decisoes adiadas**
- Flexibilidade de data por trecho (flex_days)
- Multi-city nativo como bilhete unico
- Caso D (open jaw sem retorno a origem)
- Classificacao de banda do preco total da viagem
- Suporte a trechos terrestres (declarativos, nao monitorados)

**Tres riscos principais para atencao imediata**
1. Estouro de quota da API quando multiplos Trips multi-trecho ficam ativos ao mesmo tempo. Mitigacao: guarda na Fase F e dashboard de consumo previsto.
2. Migracao de dados existentes pode corromper historico de snapshots se o mapeamento RouteGroup->Trip nao for unico. Mitigacao: rodar migracao primeiro em copia do banco e validar contagens antes de aplicar em prod.
3. Complexidade do email consolidado com multiplos trechos pode reduzir legibilidade e fazer o usuario ignorar alertas. Mitigacao: limitar MVP a secao por trecho curta, sem detalhes longos, e iterar apos primeiro uso real.
