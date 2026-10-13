# Onde podar agora — Rio de Janeiro

Ranking dos CEPs do Rio de Janeiro por prioridade de poda de árvores, com mapa de risco, feito a partir dos chamados abertos da Central 1746.

**Ver o site:** `https://heitor-oss.github.io/onde-podar-agora/`

Análise exploratória do projeto de extensão *Ciência de Dados para Cidades Inteligentes* (UFRJ). Não é um dado oficial da Prefeitura, da COMLURB nem da Light.

## O que a página mostra

- **Os 10 lugares mais urgentes** (na cidade ou em cada zona), cada um com: por que está na lista, o que pode acontecer se não for podado e quem precisa agir (COMLURB, Light ou vistoria).
- **O que pode acontecer se não podar:** árvore caída, árvore na fiação e fila crescendo, com números do 1746; quantos lugares de cada faixa de nota tiveram esses problemas no ano seguinte; e a comparação entre lugares atendidos e não atendidos a tempo.
- **Como usar a lista:** passos para a equipe.
- **Mapa de risco:** a cidade em quadrados de cerca de 1 km, com quatro camadas (quedas no verão, risco recente, conflito com a rede e prioridade de poda).
- **Todos os lugares:** 9.848 CEPs, com filtros por zona, tipo de ação e busca, ordenados pela nota da cidade ou pela posição dentro de cada zona.
- **Apêndice para quem quer entender a nota:** pesos ajustáveis, validação, teste dos pesos em 8 períodos, ideias descartadas e todos os limites.

## Como a nota é feita

Cada CEP recebe uma nota de 0 a 100, soma de cinco sinais, cada um de 0 a 1 multiplicado pelo peso:

| Sinal | Peso sugerido | Parte cheia com |
|---|---|---|
| Risco recente: chamados de avaliação de risco, remoção e árvore caída em 12 meses (queda conta em dobro) | 25 | 12 chamados |
| Poda aberta com a COMLURB (Aberto ou Em Andamento, até 2 anos) | 15 | 8 pedidos |
| Travado na Light (status Pendente) | 40 | 12 pedidos |
| Previsão de novo pedido travado na Light em 12 meses (modelo de gradient boosting por trecho de rua) | 10 | 55% de chance |
| Tempo de espera do pedido de poda mais antigo | 10 | 1 ano |

Os pesos foram escolhidos com os dados: testamos combinações com o que se sabia em julho de 2024 e ficamos com a que mais acertou o ano seguinte.

Nos sinais de contagem, cada pedido a mais vale um pouco menos que o anterior: parte = log(1 + n) / log(1 + teto).

## Validação

Nota recalculada só com o que se sabia em jan/2025 e em jul/2025 (inclusive quais pedidos estavam abertos naquelas datas); resultado nos 12 meses seguintes para os 200 CEPs do topo (média dos dois testes):

| No ano seguinte, o CEP teve… | Pesos atuais | Pesos anteriores | CEP qualquer |
|---|---|---|---|
| árvore caída | 34% | 31% | 12% |
| chamado de risco, remoção ou queda | 92% | 91% | 46% |
| novo pedido travado na Light | 65% | 62% | 19% |
| 2 ou mais pedidos de poda | 97% | 96% | 49% |

O que cada faixa de nota significa (mesmos testes):

| Nota | CEPs | árvore caída | novo pedido travado na Light |
|---|---|---|---|
| 80–100 | 44 | 47% | 71% |
| 60–79 | 312 | 28% | 59% |
| 40–59 | 1.055 | 22% | 41% |
| 20–39 | 2.686 | 14% | 23% |
| 0–19 | 5.045 | 8% | 9% |

Os pesos foram conferidos em 8 datas de corte (jan/2024 a set/2025, modelo de previsão retreinado sem ver o futuro em cada uma). Acerto médio = média do acerto em árvore caída, risco/queda e novo pedido travado na Light, nos 200, 500 e 1.000 CEPs do topo. Em todos os períodos os pesos atuais acertaram mais que os anteriores (0,7 a 2,5 pontos) e ficaram entre os 7% melhores de 3.000 combinações sorteadas. A melhor combinação nos 8 períodos juntos seria 25/10/50/10/5 (risco/poda aberta/Light/previsão/espera), 0,5 ponto acima em média, com todo o ganho em prever pedidos novos travados na Light; mantivemos 25/15/40/10/10 para dar mais peso a quem já espera poda da COMLURB, o que a medida de acerto não conta.

"Se não podar" por lugar: chance estimada por uma curva logística da nota (pesos sugeridos) ajustada às 8 datas de corte; mostrada como "x em cada 10 lugares com nota parecida". Comparação atendido × não atendido (cortes jul/2024 a abr/2025, CEPs com 2+ pedidos abertos): onde a maior parte foi atendida em até 3 meses, houve menos árvores caídas nos 9 meses seguintes em todas as faixas de nota (nota 60+: 22% contra 27%). É um indício, não uma prova.

No mapa de risco, usando o histórico até nov/2025, os 10% de quadrados com mais quedas concentraram 32% das quedas do verão 2025–26.

Testado e descartado (não melhorou o acerto): vizinhança de 150–300 m, quedas em verões anteriores no quadrado de 1 km, cobertura de árvores do setor, contagem por endereço, pedidos fechados como "não há previsão", os 3.901 pedidos fechados em massa em out/2025 e um modelo de aprendizado de máquina no lugar da soma com pesos.

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `index.html` | o site, autocontido (dados embutidos) |
| `dados/ranking_ceps_poda.csv` | ranking completo com os pesos sugeridos: nota, posição na zona, pontos de cada sinal, contagens e coordenadas do CEP |
| `dados/quedas_verao_quadrados_1km.csv` | quedas de árvore de dezembro a abril (2022–2026) por quadrado de ~1 km |
| `codigo/` | todo o código da análise: limpeza dos chamados, modelos de aprendizado de máquina, validação e montagem desta página. Comece por [`codigo/README.md`](codigo/README.md) |

## Código

A pasta [`codigo/`](codigo/) tem as 70 etapas da análise, numeradas na ordem em que rodam (A01 a J18), cada uma com um cabeçalho que explica o que faz, o que lê e o que grava. Com os CSVs dos chamados em `codigo/dados_entrada/`, `python codigo/rodar_tudo.py` refaz tudo, inclusive este site, em cerca de 12 minutos. O [`codigo/README.md`](codigo/README.md) explica como rodar, os filtros e definições usados nos dados e os modelos.

## Limites

- "Travado na Light" é o status **Pendente** do 1746, usado como aproximação de "depende da Light" (a COMLURB não poda perto de fiação energizada). Não temos o histórico de desligamentos nem o traçado da rede da Light.
- A nota mostra onde as pessoas pediram e como cada região registra os pedidos: na Zona Oeste só 5% dos pedidos de poda ficam Pendentes (20% na Grande Tijuca) e 28% são fechados como "informações incorretas" (8% na Zona Sul). A página oferece a ordenação "posição dentro de cada zona" para compensar.
- Os 500 CEPs de maior nota concentraram só 13% a 17% das árvores caídas do ano seguinte: o ranking não substitui a prontidão em dias de temporal.
- O status de cada pedido é o da data de extração; alguns pedidos antigos podem já ter sido resolvidos sem baixa no sistema. Em 13 e 14/10/2025, cerca de 4 mil pedidos antigos foram fechados em massa.
- O CEP vem da localização do chamado cruzada com a base de CEPs.

## Fonte

Chamados de manejo arbóreo da Central 1746, set/2022 a set/2026, publicados no Data.Rio (base de dados abertos da Prefeitura do Rio). Dados até 20/09/2026. Pedidos agregados por CEP; nenhum dado pessoal é exibido.
