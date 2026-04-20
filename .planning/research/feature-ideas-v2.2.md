# Flight Monitor: Feature Ideas v2.2

Lista priorizada de funcionalidades candidatas para transformar o Flight Monitor em produto com tração orgânica no Brasil. Fundamentada em `market-research-v2.1.md` e no estado atual do produto (polling 2x/dia, histórico de 90 dias, classificação LOW/MEDIUM/HIGH, auth Google, isolamento por usuário, multi-fonte SerpAPI + fast-flights). Exclusões já no radar: Telegram, WhatsApp, landing de captura, multi-trecho complexo, Kiwi Tequila.

## Tabela resumo priorizada

| # | Feature | Impacto principal | Esforço | Prioridade |
|---|---|---|---|---|
| 1 | Índice de barganha público por rota (SEO) | Aquisição orgânica | M (5-7d) | Alta |
| 2 | Card compartilhável "Preço Justo" | Viralização | S (3-4d) | Alta |
| 3 | Simulador "quanto você economizou/perdeu" | Retenção e NPS | S (2-3d) | Alta |
| 4 | Previsão de preço leve (regressão + sazonalidade) | Conversão e diferencial | M (5-8d) | Alta |
| 5 | Datas flexíveis (+/- 3 e +/- 7 dias) | Conversão | M (4-6d) | Alta |
| 6 | Grupo compartilhado entre 2 usuários | Retenção e viral K-factor | M (5-7d) | Alta |
| 7 | Destino flexível por tema ("capital europeia julho") | Aquisição e diferencial | L (8-12d) | Média |
| 8 | Radar de mistake fares comunitário | Viralização e marca | M (6-8d) | Média |
| 9 | Alerta reverso "melhor mês para ir" | Engajamento | S (3-4d) | Média |
| 10 | Digest semanal personalizado por perfil | Retenção | S (3d) | Média |
| 11 | Badge de confiança "preço coletado às HH:MM" | NPS e trust | XS (1-2d) | Média |
| 12 | Comparador público "esse preço é bom?" | Aquisição top-of-funnel | M (5-7d) | Alta |
| 13 | Integração iCal/Google Calendar (janela de compra) | Retenção | S (2-3d) | Baixa |
| 14 | Modo férias escolares BR | Engajamento segmentado | S (3d) | Média |
| 15 | API pública read-only de histórico por rota | Dev relations e SEO | M (5d) | Baixa |
| 16 | Classificação por tipo de viajante (lazer/trabalho/família) | Personalização | S (3d) | Baixa |

Top 5 recomendadas no final do documento, após matriz impacto × esforço.

## 1. Índice de barganha público por rota (SEO)

**Problema.** Usuário que ainda não conhece o Flight Monitor busca no Google "passagem GRU LIS média" ou "quando cai preço voo Recife". Hoje o produto não aparece porque não existe página pública indexável. Melhores Destinos domina essa SERP com conteúdo editorial.

**Proposta.** Gerar páginas públicas estáticas (ou com cache agressivo) por rota monitorada no formato `/rota/GRU-LIS`. Cada página mostra média de 90 dias, mínimo, máximo, desvio padrão, último preço coletado, gráfico simples (Chart.js via CDN) e CTA "monitore essa rota grátis". Sitemap automático. Conteúdo gerado por template Jinja2 a partir do histórico já existente.

**Impacto.** Aquisição orgânica de longo prazo. Melhores Destinos prova que SEO de rota funciona no BR. Cada rota vira landing individual que ranqueia por cauda longa. Efeito composto: com 200 usuários monitorando mesmo só 3 rotas cada, surgem rapidamente centenas de páginas únicas com dados que ninguém mais publica.

**Esforço.** M, 5 a 7 dias. Stack atual suporta: rota no FastAPI, template Jinja2, job diário regenerando snapshot, sitemap.xml.

**Dependência externa.** Nenhuma. Eventualmente Search Console para monitorar indexação.

**Prioridade.** Alta. É a jogada de aquisição mais barata e mais defensável porque usa um dado (histórico 90 dias por rota) que nenhum concorrente BR expõe publicamente.

## 2. Card compartilhável "Preço Justo"

**Problema.** Quem monitora rota e recebe alerta bom não tem como compartilhar a descoberta de forma visual. Usuário hoje tiraria print do email, o que é feio e não divulga o produto.

**Proposta.** Gerar imagem PNG dinâmica (Pillow no backend) com layout tipo story/feed: rota, preço atual, delta vs média 90d, classificação LOW/MEDIUM/HIGH, data do snapshot e marca d'água discreta com domínio. Botão "compartilhar" no dashboard gera URL pública única do tipo `/share/abc123.png`. Meta tags Open Graph apontando para a imagem, para que link no WhatsApp e Instagram renderize preview rico.

**Impacto.** Viralização orgânica. Cada usuário satisfeito vira distribuidor. O card carrega branding sem pedir licença, e o preview do link no WhatsApp funciona como anúncio grátis.

**Esforço.** S, 3 a 4 dias. Pillow + armazenamento dos PNGs (pode ser em disco efêmero do Render ou S3 com free tier, ou regenerar on-demand com cache).

**Dependência externa.** Nenhuma.

**Prioridade.** Alta. Quick win clássico, retorno alto por linha de código.

## 3. Simulador "quanto você economizou ou perdeu"

**Problema.** Usuário não percebe valor contínuo do produto. Após o primeiro alerta, engajamento cai. Falta reforço emocional do benefício entregue.

**Proposta.** No dashboard, para cada grupo de monitoramento ativo, mostrar bloco "Desde que você criou esse alerta há 28 dias, o preço médio foi R$ 2.340 e hoje está R$ 1.890. Se tivesse comprado no melhor momento, teria pago R$ 1.720, economia de R$ 620 vs média". Texto adaptativo conforme a trajetória. Include também no email mensal de resumo.

**Impacto.** Retenção e NPS. Aplica loss aversion de Kahneman (citado no research) de forma nativa: usuário sente que perdeu oportunidade e reforça a crença de que o produto cria dinheiro. Aumenta chance de recomendar.

**Esforço.** S, 2 a 3 dias. Só precisa de query agregada sobre preços já armazenados.

**Dependência externa.** Nenhuma.

**Prioridade.** Alta. Barato e toca direto no core value.

## 4. Previsão de preço leve com regressão e sazonalidade

**Problema.** Alerta hoje é reativo (detecta queda quando acontece). Usuário quer saber se deve esperar mais ou comprar já. Hopper e Kayak têm forecast, nenhum player BR tem.

**Proposta.** Modelo leve por rota: regressão linear com features de dias até embarque, dia da semana, mês, feriado próximo e tendência de 30 dias. Rodar scikit-learn (ou statsmodels para SARIMA simples) em job noturno por rota. Exibir "nossa projeção: preço deve subir 12% nos próximos 14 dias" no email e dashboard. Prophet só se regressão não der precisão; Prophet é pesado para Render free tier.

**Impacto.** Conversão (usuário decide agora) e diferencial competitivo. Mesmo com acurácia modesta (60%), o simples fato de ter projeção muda a experiência do alerta.

**Esforço.** M, 5 a 8 dias. Inclui validação retroativa no histórico próprio antes de expor ao usuário, com métrica pública de acerto.

**Dependência externa.** Nenhuma. Exigência de dado: pelo menos 45 dias de histórico por rota (já temos 90).

**Prioridade.** Alta. Features preditivas são o que diferencia ferramenta de newsletter.

## 5. Datas flexíveis (+/- 3 dias e +/- 7 dias)

**Problema.** Usuário que pode viajar em janela flexível não encontra hoje a melhor combinação. Criar 7 alertas manuais é fricção absurda.

**Proposta.** No formulário de grupo, checkbox "datas flexíveis" com opções +/- 3 e +/- 7. Backend expande em múltiplas queries no polling (cache compartilhado entre usuários com mesma rota). Dashboard mostra matriz de preços por data de ida x data de volta, com célula mais barata destacada.

**Impacto.** Conversão direta em uso recorrente. Segmento grande de PO que "pode viajar qualquer fim de semana de julho". Aumenta também as chances de um grupo disparar alerta (7 datas versus 1).

**Esforço.** M, 4 a 6 dias. Cuidado com custo de API: expansão combinatorial 7x7 são 49 queries. Mitigar com cache compartilhado e dedupe.

**Dependência externa.** Nenhuma, mas impacta orçamento SerpAPI. Priorizar fast-flights na expansão.

**Prioridade.** Alta. Feature esperada pelo usuário médio; ausência é percebida como falha.

## 6. Grupo compartilhado entre dois usuários

**Problema.** Casal, pai e filha, dois amigos planejando viagem juntos cada um cria seu alerta isolado. Alertas descorrelacionados geram confusão.

**Proposta.** Usuário A convida usuário B por email para um "grupo compartilhado". Ambos veem mesmo histórico, recebem mesmo alerta. Convite gera conta Google OAuth no primeiro login do convidado. Limite inicial: 2 pessoas por grupo.

**Impacto.** Retenção (uso social sustenta hábito) e K-factor viral: cada convite é um novo usuário com intenção alta. Métrica de growth típica de produto que escala sem ads.

**Esforço.** M, 5 a 7 dias. Exige ajuste no modelo de isolamento de dados (de 1:N para N:N com tabela de membership) e fluxo de convite por email. Compatível com o schema atual porque o isolamento já existe, só precisa abrir exceção controlada.

**Dependência externa.** Nenhuma.

**Prioridade.** Alta. Mecânica social é raro em ferramenta de alerta de voo; vira diferencial imediato.

## 7. Destino flexível por tema

**Problema.** Viajante com intenção vaga ("quero conhecer Europa em julho, de qualquer lugar") hoje abandona ferramentas de alerta porque todas exigem par origem/destino fixo.

**Proposta.** Presets de destino por tema: "capitais europeias", "Caribe", "América do Sul barata", "ásia exótica". Usuário escolhe origem (ou região) e tema. Backend mantém curadoria de N aeroportos por tema e faz expansão, com cache compartilhado. Alerta vem como "O destino mais barato da lista 'capitais europeias' a partir de GRU em julho é LIS a R$ 3.420".

**Impacto.** Aquisição via diferencial real (ninguém no BR faz bem) e ampliação do ICP para quem ainda não tem destino definido.

**Esforço.** L, 8 a 12 dias. Desafio é custo de API e complexidade de ranking com normalização de preço por distância.

**Dependência externa.** Nenhuma, mas pressiona budget de polling.

**Prioridade.** Média. Alto valor mas esforço também alto; depois de quick wins.

## 8. Radar de mistake fares comunitário

**Problema.** Mistake fares são o holy grail do viajante econômico (Going construiu marca neles). Hoje o Flight Monitor não identifica nem destaca essas ocorrências raras.

**Proposta.** Detecção automática: preço individual abaixo de 2 desvios padrão do histórico da rota e abaixo de 60% do menor preço do último ano dispara classificação MISTAKE. Alerta especial com prazo curto ("provavelmente corrige em 4h"). Página pública `/mistakes` com histórico anônimo dos últimos dispararam. Comunidade opcional opt-in vê alertas mistake em canal geral.

**Impacto.** Viralização e posicionamento de marca. Mistake fare é notícia, usuário compartilha espontaneamente no WhatsApp e Twitter. Gera menções.

**Esforço.** M, 6 a 8 dias. Inclui proteção contra falso positivo (preço zerado por bug da fonte).

**Dependência externa.** Nenhuma.

**Prioridade.** Média. Depende de volume de dados para detecção confiável; pode ser feature de v2.3 quando base de histórico for maior.

## 9. Alerta reverso "melhor mês para ir"

**Problema.** Usuário define data e quer preço, mas muitos casos reais são o inverso: tem 10 dias de folga até fim do ano, qual mês é mais barato?

**Proposta.** Nova modalidade de alerta: origem e destino fixos, janela de data em aberto (próximos 6 meses, fim de semana prolongado, julho inteiro). Sistema faz sampling distribuído no tempo (não precisa diário em cada dia) e recomenda melhor bloco. Email mensal com ranking de meses.

**Impacto.** Engajamento de quem estaria inativo entre viagens. Fica no produto mesmo sem viagem específica planejada.

**Esforço.** S, 3 a 4 dias reusando multi-fonte.

**Dependência externa.** Nenhuma.

**Prioridade.** Média.

## 10. Digest semanal personalizado por perfil

**Problema.** Usuário cria 2 grupos e depois some. Sem cadência, o produto perde lembrete de existir.

**Proposta.** Email de segunda às 9h com resumo dos alertas da semana do usuário, top 3 oportunidades nas rotas dele, estatística comparativa ("você monitora 3 rotas, a mais promissora agora é GRU-MCZ"). Tom editorial curto, não genérico.

**Impacto.** Retenção. Rítmo previsível (Going valida o padrão). Não compete com Melhores Destinos porque é personalizado, não broadcast.

**Esforço.** S, 3 dias. Template Jinja2 + job segunda-feira.

**Dependência externa.** Nenhuma (infra de email já existe).

**Prioridade.** Média.

## 11. Badge de confiança com timestamp da coleta

**Problema.** Usuário desconfia de alerta sem saber de onde veio preço. Confiança é frágil em deal alerts.

**Proposta.** Em todos os alertas e páginas, mostrar "Preço coletado de Google Flights às 14:32 de 19/04/2026. Link direto para companhia aérea: [x]". Item já sugerido no research. Pequeno, mas gera diferencial de confiança.

**Impacto.** NPS e credibilidade. Reduz churn por desconfiança.

**Esforço.** XS, 1 a 2 dias.

**Dependência externa.** Nenhuma.

**Prioridade.** Média por esforço muito baixo.

## 12. Comparador público "esse preço é bom?"

**Problema.** Quem não é usuário encontra preço em algum site e quer validar rapidamente se está bom. Não tem como consultar o Flight Monitor sem criar conta.

**Proposta.** Página pública `/vale-a-pena` com formulário: origem, destino, preço, data. Retorna comparação com histórico do Flight Monitor ("esse preço é 8% acima da média dos últimos 90 dias, não compre ainda" ou "ótimo, 22% abaixo da média"). Sem necessidade de login. CTA para criar monitoramento contínuo.

**Impacto.** Aquisição top of funnel. Usuário conhece o produto resolvendo dor pontual, vira lead.

**Esforço.** M, 5 a 7 dias. Inclui rate limiting anti abuso e fallback quando rota não está no histórico.

**Dependência externa.** Nenhuma.

**Prioridade.** Alta. Funciona em conjunto com feature 1 (SEO por rota): usuário cai da busca orgânica, usa o comparador, vira usuário.

## 13. Integração iCal e Google Calendar com janela de compra

**Problema.** Quando o sistema detecta janela ótima, usuário pode esquecer ou atrasar decisão.

**Proposta.** Botão "adicionar ao calendário" no alerta LOW: gera evento iCal de 2 horas com título "Comprar GRU-LIS agora" e link direto. Funciona em qualquer cliente de calendário.

**Impacto.** Retenção em micro-momentos críticos e conversão da decisão.

**Esforço.** S, 2 a 3 dias.

**Dependência externa.** Nenhuma. Sem OAuth de calendário, apenas arquivo .ics.

**Prioridade.** Baixa. Nice to have.

## 14. Modo férias escolares BR

**Problema.** Público família no Brasil concentra viagens em janeiro, julho e recesso de outubro. Produto genérico não se posiciona para esse segmento.

**Proposta.** Switch no grupo: "modo férias escolares". Sistema automaticamente monitora preços para janelas de julho e janeiro, começa polling 4 meses antes, e ajusta classificação LOW/MEDIUM/HIGH para a sazonalidade dessas janelas (preços são estruturalmente mais altos).

**Impacto.** Engajamento segmentado. Segmento grande e subatendido.

**Esforço.** S, 3 dias.

**Dependência externa.** Nenhuma.

**Prioridade.** Média.

## 15. API pública read-only de histórico por rota

**Problema.** Nicho dev e blogueiros de viagem precisam de dados, hoje não têm fonte pública brasileira.

**Proposta.** Endpoint `/api/v1/routes/{origin}-{dest}/history` retornando JSON com preços dos últimos 90 dias, com rate limit e key opcional. Documentação swagger pública.

**Impacto.** Dev relations, citações em posts, backlinks de qualidade, autoridade de domínio para SEO. Impacto indireto mas composto.

**Esforço.** M, 5 dias. FastAPI já suporta swagger nativo.

**Dependência externa.** Nenhuma.

**Prioridade.** Baixa. Depois de maturar histórico.

## 16. Classificação por tipo de viajante

**Problema.** Mesma rota tem valor diferente para viajante de lazer e executivo. Classificação LOW genérica não captura.

**Proposta.** No onboarding, usuário escolhe tipo de viagem por grupo: lazer, trabalho, família. Classificação ajusta pesos (ex: viagem família prioriza bagagem despachada no preço comparativo; trabalho prioriza horário comercial).

**Impacto.** Personalização percebida.

**Esforço.** S, 3 dias.

**Dependência externa.** Nenhuma.

**Prioridade.** Baixa.

## Matriz impacto × esforço

```
           Esforço baixo (XS/S)         Esforço médio (M)           Esforço alto (L/XL)
Impacto   |                           |                           |
alto      | 2 Card compartilhável     | 1 Índice barganha SEO     | 7 Destino flexível tema
          | 3 Simulador economia      | 4 Previsão de preço       |
          | 9 Alerta reverso melhor   | 5 Datas flexíveis         |
          |   mês                     | 6 Grupo compartilhado     |
          |                           | 12 Comparador público     |
----------+---------------------------+---------------------------+--------------------------
Impacto   | 10 Digest semanal         | 8 Radar mistake fares     |
médio     | 11 Badge confiança        | 15 API pública            |
          | 14 Modo férias escolares  |                           |
----------+---------------------------+---------------------------+--------------------------
Impacto   | 13 iCal                   |                           |
baixo     | 16 Tipo viajante          |                           |
          |                           |                           |
```

## Top 5 recomendadas

1. **Card compartilhável "Preço Justo"** (#2). Melhor relação viralização/esforço. Ativa canal orgânico (WhatsApp e Instagram) sem depender de provider.
2. **Simulador economia** (#3). Reforça core value no produto, barato, amplia NPS.
3. **Índice de barganha público por rota** (#1). Fundação de SEO de longo prazo que amplia aquisição sem ads.
4. **Previsão de preço leve** (#4). Diferencial competitivo real versus Melhores Destinos e Passagens Imperdiveis; cobre gap do research.
5. **Grupo compartilhado entre 2 usuários** (#6). Mecânica viral nativa, converte usuário satisfeito em canal de distribuição.

Sequência sugerida para execução: 2, 3, 11 (XS grátis), 1, 12, 4, 5, 6, 14, 10, 9, 8, 7, 15, 13, 16. Revisitar após atingir 50 usuários ativos para recalibrar prioridades com base em dados reais de uso.
