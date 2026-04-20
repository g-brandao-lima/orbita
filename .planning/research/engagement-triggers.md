# Flight Monitor - Gatilhos de Engajamento, Retenção e Conversão

Documento de estratégia comportamental para Flight Monitor, sistema brasileiro de alerta de passagens aéreas. Objetivo: aumentar CTR de alertas, retenção, criação de grupos, compartilhamento orgânico e conversão para afiliado, sem dark patterns. Toda mecânica só funciona se sustentada por dado real. Produto de viagem tem ticket caro, arrependimento mata LTV.

---

## 1. Gatilhos de abertura de e-mail

### 1.1 Subject line com número específico e rota

**Mecânica**: subject traz variação percentual real, rota e janela temporal. Nada de "imperdível", "aproveite", "última chance".

**Dado que sustenta**: estudos de e-mail marketing (Mailchimp, HubSpot) mostram que subjects com números concretos e personalização por rota/cidade aumentam open rate de forma consistente em segmentos de utilidade. No Brasil, E-goi e RD Station indicam que personalização de rota (origem do usuário) é um dos maiores drivers de abertura.

**Implementação**:
- "GRU-LIS caiu 23% hoje (R$ 3.120, média 90d: R$ 4.050)"
- "Seu grupo Lua de Mel Europa tem novo menor preço"
- "Preço de GRU-MIA voltou ao patamar de janeiro"

Regra: número no subject sempre casa com o corpo do e-mail e com o dashboard. Se não caiu 23% de verdade, não escreve 23%.

**Impacto esperado**: maior open rate vs subjects genéricos; maior confiança de longo prazo porque o número sempre entrega.

**Risco ético**: baixo, desde que o pipeline de dados garanta veracidade. Mitigação: guard no backend que impede envio se o cálculo da variação falhar ou vier de amostra pequena (menos de N observações em 90 dias).

**Prioridade**: alta.

### 1.2 Preview text que complementa, não repete

**Mecânica**: preview text (primeiras linhas visíveis na caixa) traz a informação que o subject não coube dizer. Subject dá o "o quê", preview dá o "por que agora".

**Implementação**:
- Subject: "GRU-LIS caiu 23% hoje"
- Preview: "Menor preço desde janeiro. Saída 12/set, TAP direto."

**Impacto esperado**: open rate marginalmente maior e, principalmente, CTR dentro do e-mail porque o usuário já chega contextualizado.

**Risco ético**: baixo. Mitigação: nunca usar preview text para criar urgência falsa ("últimas horas" sem base).

**Prioridade**: alta.

### 1.3 Horário e frequência

**Mecânica**: enviar alertas de queda em até 30 minutos após detecção (valor da informação decai rápido). Digest semanal em horário de planejamento (terça ou quarta, entre 19h e 21h horário de Brasília, quando o usuário está em casa pensando em férias).

**Dado que sustenta**: relatórios de e-mail Brasil (E-goi, RD Station, Mailjet) apontam terça e quarta à noite como janelas fortes para conteúdo de lazer e planejamento pessoal.

**Frequência máxima**: 1 alerta por grupo por dia (se houver múltiplas quedas, consolidar). 1 digest semanal. Nunca mais de 3 e-mails por semana por usuário, somados todos os grupos. Acima disso, entra em modo "resumo diário único".

**Risco ético**: excesso de e-mail vira spam e queima o canal. Mitigação: cap duro por usuário, com configuração visível no dashboard ("receber até X alertas por semana").

**Prioridade**: alta.

---

## 2. Gatilhos dentro do dashboard

### 2.1 Sparkline de tendência por grupo

**Mecânica**: cada card de grupo monitorado mostra um gráfico mínimo (sparkline) dos últimos 30 ou 90 dias, com ponto atual destacado. Cor neutra quando estável, verde quando abaixo da média, âmbar quando subindo.

**Dado que sustenta**: Hopper popularizou o gráfico de confiança como gatilho visual. Edward Tufte documenta sparklines como a forma mais densa de mostrar tendência sem poluir.

**Implementação**: SVG inline gerado no Jinja2, sem JS. Tooltip no hover mostra "Hoje: R$ 3.120. Média 30d: R$ 3.870."

**Impacto esperado**: usuário abre o dashboard e em 2 segundos sabe onde olhar. Reduz bounce e aumenta clique nos grupos relevantes.

**Risco ético**: nenhum, é informação pura. Mitigação não se aplica.

**Prioridade**: alta.

### 2.2 Badges factuais

**Mecânica**: badge textual no card quando o preço atual cruza um limiar real.

**Exemplos**:
- "Menor preço em 30 dias"
- "Abaixo da média dos últimos 90 dias"
- "Subiu nos últimos 7 dias"
- "Estável há 14 dias"

Implementação: badge só aparece se a condição for verdadeira no momento do render. Nunca sticky.

**Impacto esperado**: aumenta CTR do card específico e a confiança geral do produto ("esse site não enche linguiça").

**Risco ético**: baixo se badges forem regidos por regras determinísticas. Mitigação: lista fechada de badges, cada um com função pura que retorna booleano a partir do histórico.

**Prioridade**: alta.

### 2.3 Microcopy de botões e títulos

**Mecânica**: substituir verbos genéricos por verbos de ação contextual.

- Em vez de "Criar grupo", usar "Monitorar nova rota".
- Em vez de "Ver detalhes", usar "Ver histórico de preço".
- Em vez de "Salvar", usar "Começar a monitorar".
- Título do dashboard: "Suas rotas monitoradas" em vez de "Dashboard".

**Impacto esperado**: CTR marginalmente maior e menor fricção cognitiva.

**Risco ético**: nenhum.

**Prioridade**: média.

### 2.4 Estado vazio que convida

**Mecânica**: primeiro login, nenhum grupo criado. Em vez de tela vazia, mostrar 6 rotas populares clicáveis com histórico real já carregado.

**Implementação**:
- "Ainda não monitorando nenhuma rota. Comece por uma dessas."
- Cards com GRU-LIS, GRU-MIA, GRU-EZE, GIG-CDG, REC-LIS, GRU-SCL, cada um com sparkline real dos últimos 90 dias e botão "Monitorar esta rota".

**Impacto esperado**: taxa de ativação (primeiro grupo criado) bem maior que tela vazia padrão.

**Risco ético**: nenhum. Mitigação: rotas sugeridas precisam de dado real.

**Prioridade**: alta.

### 2.5 Onboarding em menos de 60 segundos

**Mecânica**: fluxo linear de 3 passos após login Google: (1) escolher rota (autocomplete com aeroportos BR no topo), (2) janela de datas aproximada ou flexível, (3) confirmar. Sem tutorial, sem tour, sem modal de boas-vindas.

**Implementação**: form único, sem etapas navegadas. Campos autofocáveis por tab.

**Impacto esperado**: ativação alta, pouca evasão.

**Prioridade**: alta.

---

## 3. Gatilhos de criação de novos grupos

### 3.1 Sugestões contextuais baseadas em cohort

**Mecânica**: se o usuário monitora GRU-LIS, sugerir abaixo "Quem monitora GRU-LIS também monitora GRU-OPO e GRU-MAD". Só exibir quando houver N usuários suficientes no cohort (privacidade e estatística).

**Dado que sustenta**: recomendação por cohort é padrão em marketplaces e agregadores (Amazon, Skyscanner).

**Implementação**: query batch diária gera tabela de co-ocorrência por rota. Cap mínimo de 20 usuários no cohort para exibir.

**Impacto esperado**: aumento médio de grupos por usuário ativo.

**Risco ético**: baixo. Mitigação: nunca expor identidade, só agregado.

**Prioridade**: média.

### 3.2 Templates de grupo prontos

**Mecânica**: na tela de criação, oferecer atalhos como "Carnaval 2026", "Lua de mel Europa verão", "Réveillon Caribe", "Férias de julho Nordeste". Cada template preenche janela de datas e região de destino, usuário só escolhe origem.

**Implementação**: 6 a 8 templates fixos, revisados trimestralmente conforme calendário.

**Impacto esperado**: reduz fricção de decisão "não sei nem que datas colocar".

**Risco ético**: nenhum.

**Prioridade**: média.

### 3.3 Friction reducers

**Mecânica**: autocomplete de aeroporto com os 15 mais populares no topo. Campo de data aceita "flexível +/- 3 dias" por padrão. Botão "monitorar também a volta" pré-marcado para rotas de lazer.

**Impacto esperado**: tempo de criação de grupo menor, mais grupos por sessão.

**Prioridade**: alta.

---

## 4. Gatilhos de retenção

### 4.1 Weekly digest útil

**Mecânica**: e-mail semanal, terça à noite, com 3 blocos: (1) o que mudou nos seus grupos (quedas, altas, estabilidade), (2) 1 destino em alta da semana com base em dados reais do agregador, (3) 1 dica curta de aeroporto, bagagem ou janela de compra.

**Dado que sustenta**: Going e Melhores Destinos provam que curadoria semanal retém. A diferença é que o digest do Flight Monitor é personalizado pelos grupos reais do usuário, não genérico.

**Implementação**: template Jinja2, gerado por cron domingo à noite, enviado terça.

**Impacto esperado**: retenção mensal maior e reativação de usuários que não abriam o site há semanas.

**Risco ético**: baixo. Mitigação: opt-out de 1 clique visível no rodapé.

**Prioridade**: alta.

### 4.2 Marcos temporais de viagem

**Mecânica**: se o grupo tem janela de datas específica, disparar nudge em marcos reais: 90 dias antes ("janela boa de compra começa a abrir"), 45 dias ("preços tendem a se estabilizar"), 21 dias ("última janela antes do encarecimento típico").

**Dado que sustenta**: estudos do próprio Hopper e da Expedia mostram janelas de compra ótimas (60 a 90 dias antes para internacional, 30 a 60 para doméstico). A mecânica só anuncia o marco, não garante queda.

**Implementação**: microcopy cuidadoso. "Faltam 45 dias para sua janela GRU-LIS. Historicamente, os preços se estabilizam a partir daqui."

**Impacto esperado**: retenção emocional, usuário sente que o sistema "lembra" da viagem dele.

**Risco ético**: moderado se prometer queda. Mitigação: nunca prometer, só contextualizar com base histórica.

**Prioridade**: alta.

### 4.3 Revival de grupo silenciado

**Mecânica**: se um grupo está há 30+ dias sem variação relevante, e o usuário não abre o dashboard há 14 dias, mandar um único e-mail "Seu grupo GRU-LIS está estável há 5 semanas. Quer manter, pausar ou ajustar janela?".

**Implementação**: 3 CTAs no e-mail, cada um leva a uma ação em um clique com token assinado.

**Impacto esperado**: reduz grupos zumbis e reativa usuário.

**Risco ético**: nenhum.

**Prioridade**: média.

---

## 5. Gatilhos sociais e virais

### 5.1 Card de economia compartilhável

**Mecânica**: quando o usuário marca "comprei por R$ X", gerar uma imagem (PNG via Pillow ou similar) com "Economizei R$ 1.200 em GRU-LIS acompanhando o preço por 47 dias. Flight Monitor." Usuário baixa e posta onde quiser.

**Dado que sustenta**: Wise, Nubank e Revolut usam cards de economia e marcos financeiros como motor viral.

**Implementação**: rota `/share/card/<grupo_id>` gera PNG server-side. Usuário opta explicitamente por marcar compra.

**Impacto esperado**: compartilhamento orgânico em Instagram stories e grupos de WhatsApp de viagem.

**Risco ético**: baixo. Mitigação: nunca gerar card sem ação explícita do usuário; nunca expor dado de outro usuário.

**Prioridade**: média.

### 5.2 Convite com valor explícito

**Mecânica**: "Indique 2 amigos e ganhe 3 grupos extras de monitoramento." Plano gratuito tem cap (digamos, 5 grupos); indicação desbloqueia mais.

**Implementação**: link de convite único por usuário, contabiliza quando o convidado cria o primeiro grupo (não só cadastro). Limite máximo de recompensas para evitar gaming.

**Impacto esperado**: k-factor positivo em nicho de viagem.

**Risco ético**: baixo, desde que a entrega do benefício seja automática e visível. Mitigação: regras na landing de convite em linguagem clara.

**Prioridade**: média.

### 5.3 Histórico público por rota (SEO)

**Mecânica**: página pública `/rota/GRU-LIS` mostra gráfico de preço médio dos últimos 12 meses, faixa de mínimos, dica de janela. Indexável, linkável, compartilhável.

**Dado que sustaina**: Melhores Destinos e Kayak Trends construíram audiência orgânica com páginas de rota. Google ama conteúdo de dado estruturado.

**Implementação**: rota Jinja2 com cache de 24h. Schema.org para FAQ e histórico.

**Impacto esperado**: tráfego orgânico de longo prazo, backlink natural, credibilidade.

**Prioridade**: média (alta se for otimizar custo de aquisição).

---

## 6. Gatilhos de conversão para afiliado

### 6.1 Botão "Ver oferta" contextualizado

**Mecânica**: CTA principal não é "Comprar agora" (parece OTA). É "Ver oferta atual na [companhia X]" com preço real ao lado. Usuário sabe para onde está indo.

**Implementação**: botão abre em nova aba com link afiliado. Pequeno label "link de parceria, ajuda a manter o Flight Monitor" abaixo, transparente.

**Impacto esperado**: CTR de afiliado maior porque não gera sensação de empurrão de venda.

**Risco ético**: baixo. Mitigação: disclosure clara de afiliação, política de transparência linkada.

**Prioridade**: alta.

### 6.2 Urgência legítima

**Mecânica**: contagem regressiva só aparece para fatos reais. "Voo parte em 3 dias" (fato). "Assentos classe econômica restantes segundo API: 4" (se a API expõe, senão não mostra). Nunca timer inventado.

**Implementação**: componente só renderiza se há dado de origem confiável.

**Impacto esperado**: conversão saudável sem arrependimento.

**Risco ético**: alto se mal implementado. Mitigação: política de produto proíbe qualquer timer sem fonte de verdade auditável.

**Prioridade**: alta.

### 6.3 Prova de dados ao lado do CTA

**Mecânica**: ao lado do botão de oferta, mostrar "Esse preço está 23% abaixo da média dos últimos 90 dias" ou "É o menor preço dos últimos 60 dias". Se não há vantagem, não se fabrica uma; mostra-se "preço dentro da média".

**Implementação**: label calculada no backend no mesmo request do preço.

**Impacto esperado**: conversão maior quando há vantagem; zero arrependimento quando não há, o que protege LTV.

**Risco ético**: baixo. Mitigação: honestidade inclui admitir quando não é bom momento.

**Prioridade**: alta.

---

## Resumo de priorização

**Alta**: subject line factual, preview complementar, cap de frequência, sparkline, badges, estado vazio com sugestões, onboarding em 60s, friction reducers, weekly digest, marcos temporais, CTA contextualizado, urgência legítima, prova de dados.

**Média**: microcopy refinado, cohort de sugestões, templates prontos, revival de grupos, card compartilhável, convite com recompensa, histórico público por rota.

**Baixa**: (nada neste documento é baixa; tudo aqui passou pelo filtro de verdade e utilidade).

A tese do Flight Monitor é simples: num mercado poluído de urgência fake e copy inflada, o produto que diz só a verdade vence por retenção. Todo gatilho deste documento é vinculado a dado real; nenhum depende de truque cognitivo.
