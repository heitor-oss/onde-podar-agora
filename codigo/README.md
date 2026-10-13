# Códigos do projeto de poda e rede elétrica (Central 1746, Rio de Janeiro)

Este pacote reúne **todo o código usado na análise**: leitura e limpeza dos chamados do 1746, montagem das tabelas, modelos de aprendizado de máquina, testes de validação e a montagem da página "Onde podar agora". Cada etapa é um arquivo Python separado, numerado na ordem em que deve rodar, com um cabeçalho que diz o que faz, o que lê, o que grava e onde o resultado foi usado.

Análise exploratória do projeto de extensão *Ciência de Dados para Cidades Inteligentes* (UFRJ), com dados abertos do 1746.

## Como rodar

1. **Instale o Python 3.11 ou mais novo** e as bibliotecas:
   ```
   pip install -r requirements.txt
   ```
2. **Coloque os arquivos de entrada em `dados_entrada/`** (veja a tabela abaixo). O clima e os pluviômetros já vêm no pacote; os chamados e os setores censitários, não, por serem grandes.
3. **Rode tudo:**
   ```
   python rodar_tudo.py
   ```
   Na conferência, levou cerca de 12 minutos; num notebook comum pode levar o dobro. Para rodar só uma parte: `python rodar_tudo.py J` (grupo J), `python rodar_tudo.py H02 H03` (etapas específicas) ou `python rodar_tudo.py --a-partir H01`.
4. **Veja os resultados:**
   - `trabalho/`: arquivos intermediários (`.pkl`, `.npz`) e resultados em `.json`;
   - `logs/`: o que cada etapa imprimiu (tabelas, métricas, conferências);
   - `saidas/`: planilhas finais e a página (`saidas/site/index.html`).

### Arquivos de entrada

| Arquivo em `dados_entrada/` | O que é | Vem no pacote? |
|---|---|---|
| `chamados_completo_com_cep_parte1de4.csv` … `parte4de4.csv` | Chamados de manejo arbóreo do 1746 (set/2022 a set/2026), com CEP, setor censitário e coordenada já atribuídos | Não (≈ 85 MB) |
| `dados_finais_setor_v3_subtipos1a9.csv` | Setores censitários: bairro, região administrativa, população, área, cobertura de árvores, área construída | Não (≈ 3 MB) |
| `clima_diario_rio_openmeteo.csv` | Clima diário da cidade (chuva média e máxima, maior chuva em 1 hora, maior rajada), da API histórica do Open-Meteo | Sim |
| `clima_estacoes_rio.zip` | Pluviômetros do Alerta Rio e da WebSirene, baixados do BigQuery do Data.Rio com `notebooks/clima_estacoes_datario.ipynb` | Sim |

O clima do Open-Meteo foi consultado para vários pontos da cidade e resumido por dia (média e máximo entre os pontos). A lista exata de pontos não ficou registrada; para atualizar o clima, refaça a consulta na [API histórica do Open-Meteo](https://open-meteo.com/en/docs/historical-weather-api) e mantenha as mesmas colunas.

## Estrutura

```
codigo/
├── README.md                ← este guia
├── requirements.txt
├── rodar_tudo.py            ← roda as etapas em ordem
├── etapas/                  ← uma etapa por arquivo (A01 … J18) + _comum.py (caminhos)
├── dados_entrada/           ← arquivos de entrada
├── pagina/                  ← modelo HTML da página "Onde podar agora"
├── notebooks/               ← notebook que baixa os pluviômetros do Data.Rio
├── trabalho/                ← criado ao rodar: intermediários e resultados
├── saidas/                  ← criado ao rodar: planilhas e página
└── logs/                    ← criado ao rodar: saída de texto de cada etapa
```

## Que etapa responde a qual pergunta

| Grupo | Pergunta ou produto | Etapas principais | Onde aparece |
|---|---|---|---|
| A | Preparar os dados | A01–A04 | base de tudo |
| B | Onde e quando há picos de chamados por CEP? Dá para prever? | B03, B04, B05, B07, B08 | página "Picos de chamados por CEP"; modelo 2 |
| C | O clima ajuda a prever? | C01, C02, C03 | página de picos; modelo 2 |
| D | Em quanto tempo um pedido não atendido vira emergência? | D01, D03, D04, D05 | página de picos |
| E | Dado um temporal, onde caem as árvores? | E01, E02, E04 | página de picos |
| F | Onde as equipes devem ficar de prontidão? | F01, F02, F03 | página de picos; modelo 3 |
| G | A cobertura de árvores ajuda? Quem liga menos? | G02, G03 | limites |
| H | Árvores na fiação: dá para prever onde? | H01, H02, H03, H04, H05 | página "Árvores e rede elétrica"; modelo 1 |
| I | Dá para ter menos desligamentos agrupando a poda? | I03, I06, I07 | página Light; painel do piloto |
| J | Onde podar primeiro, e por quê? | J01–J04, J07–J09, J11–J18 | página e site "Onde podar agora" |

## Limpeza e filtros aplicados

Estes são os filtros e definições que aparecem ao longo do código. Vale conferir antes de reusar.

- **Junção:** as quatro partes são lidas na ordem 1, 2, 4, 3 (a ordem da análise original). Nenhuma contagem depende disso, mas alguns desempates sim; manter a ordem reproduz os números publicados.
- **Datas:** `d` é o dia do chamado (sem hora). Pedidos ainda abertos têm a duração contada até 20/09/2026, último dia dos dados.
- **Coordenadas:** usa-se `latitude_usada` e `longitude_usada`. Nas análises por quadrado, ficam só os pontos dentro do retângulo do município (latitude −23,10 a −22,73; longitude −43,80 a −43,09).
- **Quadrado de ~1 km:** `gx = int((lon + 43,8) × 102,5)` e `gy = int((lat + 23,1) × 110,6)`.
- **Trecho de rua:** `id_logradouro` + parte inteira de `numero_logradouro ÷ 100` (números de porta 0–99, 100–199…). Só entram chamados com número de porta entre 1 e 99.999.
- **Pedidos de poda:** subtipos que contêm "Poda" (`Poda de árvore em logradouro`, `em vias públicas`, `Poda e remoção`, `Árvore - Poda`).
- **"Depende da Light":** pedido de poda com status `Pendente` (coluna `pend`). É uma aproximação: a COMLURB não poda perto de fiação energizada e esses pedidos ficam parados.
- **Atendido:** status `Fechado com solução` ou `Fechado com providências`. **Aberto:** `Aberto` ou `Em Andamento`.
- **Aberto numa data passada:** criado antes da data e sem fechamento, ou fechado depois dela (usa `data_fim`). Isso evita usar o status de hoje para o passado.
- **Fechamento em massa:** pedidos de poda fechados como `Fechado com providências` em 13 ou 14/10/2025 depois de mais de 180 dias de espera (cerca de 3.900). Testados em J06 e deixados fora da nota.
- **Emergência:** `Retirada de árvore caída` e `Avaliação de risco de queda da árvore`.
- **Pico emergencial por CEP:** 3 ou mais chamados de emergência em pelo menos 2 endereços diferentes no mesmo CEP e dia. **Pico de volume:** 5 ou mais chamados sem ser emergencial ("lote" se em até 2 endereços, "mutirão" se em mais).
- **Dia de temporal:** 40 ou mais árvores caídas na cidade no dia (E e G usam 20 ou mais).
- **Zona da cidade:** pela região administrativa; RA desconhecida entra como Norte em `P.pkl`. No ranking por CEP, aparece como "zona não identificada".

## Modelos de aprendizado de máquina

| Modelo | Pergunta | Técnica | Etapas |
|---|---|---|---|
| Modelo 1 | Quais trechos terão novo pedido que depende da Light em 12 meses? | Gradient boosting (`HistGradientBoostingClassifier`: 400 árvores, taxa 0,04, até 31 folhas, 40 trechos por folha, L2 = 1) | H02, H03; aplicado em H06, J01, J07, J11 |
| Modelo 2 | Quais CEPs terão pico emergencial amanhã? | Regressão logística (log(1+x), padronização, C = 0,3, pesos balanceados) com amostra de dias sem pico | B07, C03 (com clima); B06 e C05 foram testados e descartados |
| Modelo 3 | Onde ficar de prontidão amanhã? | Regressão de Poisson por quadrado-dia, com interações histórico × clima | F02 |
| Nota de prioridade | Onde podar primeiro? | Soma ponderada de 5 sinais em escala log; pesos escolhidos por busca e testados em 8 períodos | J03, J07–J13; J10 testou gradient boosting e descartou |

A explicação didática dos três modelos está no documento "Aprendizado de máquina no projeto de poda".

## Reprodutibilidade

- Todas as sementes aleatórias estão fixas no código (`random_state=0`, `default_rng(0)` etc.).
- O pacote foi rodado do zero, a partir dos CSVs originais, e os resultados em `.json` foram comparados com os da análise original (veja a seção "Conferência" no fim).
- Datas fixas: o fim dos dados (20/09/2026) e a data "de hoje" do ranking (21/09/2026) estão escritos dentro das etapas que os usam. Para rodar com dados mais novos, procure por `2026-09-20` e `2026-09-21` nos arquivos de `etapas/` e troque pela nova data.

## Sobre o formato dos scripts

- As etapas são os scripts usados na análise, com o mínimo de mudança: só os caminhos de arquivo foram centralizados em `etapas/_comum.py` e cada uma ganhou o cabeçalho explicativo. Os nomes de variáveis e as mensagens impressas seguem os originais (muitos estão abreviados ou em inglês).
- Algumas etapas reaproveitam o começo de outra com `exec(open(etapa('…')).read().split('…')[0])`. Por exemplo, J01 roda a parte de H02 que monta as variáveis do modelo 1. Por isso, não mude os trechos usados como marcadores (`def label`, `origins=`, `res={}`, `rows=[]`, `R={}`) sem ajustar quem os usa.
- Etapas marcadas como **exploratório** ou **teste descartado** ficaram no pacote para registro: mostram o caminho da análise e as alternativas que não deram certo.
- As páginas "Picos de chamados por CEP", "Árvores e rede elétrica" e o "Painel do piloto" foram montadas a partir dos `.json` gerados aqui, mas o código de montagem dessas páginas não foi guardado em arquivo. A página "Onde podar agora" é montada pela etapa J18.

## Todas as etapas
Tipos: **principal** (gera resultado usado nas páginas ou documentos), **exploratório** (passo intermediário da análise), **teste descartado** (alternativa testada e abandonada) e **biblioteca** (código reaproveitado por outras etapas, não roda sozinho).

### A — Preparação dos dados
- **A01 · Juntar as 4 partes dos chamados do 1746** — *principal* · `etapas/A01_juntar_chamados.py`  
  Lê os quatro CSVs de chamados (com CEP já atribuído), junta numa tabela só e cria a coluna d (dia do chamado).  
  Lê: 4 partes dos chamados (dados_entrada). Grava: full.pkl.  
  Usado em: Base de todas as análises.
- **A02 · Base de poda com datas, bairros, RAs e zonas** — *principal* · `etapas/A02_base_poda_bairros_zonas.py`  
  Converte datas de abertura e fechamento, calcula a duração (pedidos abertos contam até 20/09/2026), traz bairro e região administrativa pelo setor censitário, separa os pedidos de poda e marca pend = status Pendente (aproximação de "depende da Light"). Classifica a zona da cidade pela RA; RA desconhecida entra como Norte.  
  Lê: full.pkl, setor censitário (dados_entrada). Grava: P.pkl, df.pkl.  
  Usado em: Todas as análises de poda e Light; ranking.
- **A03 · Clima diário da cidade (Open-Meteo)** — *principal* · `etapas/A03_clima_openmeteo.py`  
  Lê o clima diário (chuva média, chuva máxima, maior chuva em 1 hora, maior rajada, chuva dos 3 e 7 dias anteriores) e confere as somas.  
  Lê: clima Open-Meteo (dados_entrada). Grava: clima.pkl.  
  Usado em: Modelos 2 e 3, sazonalidade.
- **A04 · Pluviômetros do Alerta Rio e WebSirene (Data.Rio)** — *principal* · `etapas/A04_clima_estacoes.py`  
  Lê os arquivos diários dos pluviômetros baixados do BigQuery do Data.Rio (notebook em notebooks/), filtra dias com registros suficientes e junta com as coordenadas das estações.  
  Lê: pluviômetros Data.Rio (dados_entrada). Grava: estacoes.pkl, estacoes_diario.pkl.  
  Usado em: Pergunta "dado um temporal, onde caem as árvores" (E).

### B — Picos de chamados por CEP
- **B01 · Exploração: dias de pico na cidade** — *exploratório* · `etapas/B01_explorar_picos_da_cidade.py`  
  Compara o total de chamados de cada dia com a mediana das 4 semanas anteriores e lista os maiores dias de quedas.  
  Lê: full.pkl. Grava: nada (só imprime).  
  Usado em: Primeira exploração; não gera arquivo.
- **B02 · Exploração: quantos endereços por CEP-dia** — *exploratório* · `etapas/B02_explorar_pontos_por_cep_dia.py`  
  Conta, para cada CEP e dia, quantos chamados e quantos pontos diferentes houve, para separar vários chamados sobre a mesma árvore de problemas espalhados.  
  Lê: full.pkl. Grava: nada (só imprime).  
  Usado em: Definição de pico.
- **B03 · Tabela CEP × dia e matrizes de chamados** — *principal* · `etapas/B03_tabela_cep_dia_e_matrizes.py`  
  Monta matrizes CEP × dia com todos os chamados, as quedas e os pedidos de avaliação de risco, a tabela cepday (chamados, pontos, quedas, horário, bairro, rua) e marca os dias de temporal (40 ou mais quedas na cidade).  
  Lê: full.pkl. Grava: cepday.pkl, mats.npz, peaks.pkl.  
  Usado em: Picos por CEP, modelo 2, clima.
- **B04 · Picos por CEP e o que acontece antes deles** — *principal* · `etapas/B04_eventos_e_perfil_antes_do_pico.py`  
  Define pico emergencial (3+ chamados de queda ou risco em 2+ endereços no mesmo CEP e dia) e picos de volume (5+ chamados, "lote" no mesmo endereço ou "mutirão" na rua). Compara os chamados nos dias anteriores ao pico com CEPs sorteados.  
  Lê: cepday.pkl, mats.npz. Grava: ev.pkl, prof.json, vol.pkl.  
  Usado em: Página "Picos de chamados por CEP".
- **B05 · Antes do pico × o próprio CEP em outras épocas** — *principal* · `etapas/B05_comparacao_com_o_proprio_cep.py`  
  Compara os 30 dias antes de cada pico com janelas sorteadas do mesmo CEP longe do pico.  
  Lê: ev.pkl, mats.npz, vol.pkl. Grava: selfctl.json.  
  Usado em: Página "Picos de chamados por CEP".
- **B06 · Modelo 2 com gradient boosting (descartado)** — *teste descartado* · `etapas/B06_modelo2_picos_gbm.py`  
  Treina gradient boosting para prever picos por CEP-dia com amostragem de dias sem pico. Com só 57 picos no treino, decorou os exemplos e foi pior que a regressão logística. Define as variáveis usadas pelos passos seguintes.  
  Lê: ev.pkl, mats.npz, vol.pkl. Grava: model.json.  
  Usado em: Comparação; base de B07 e C03.
- **B07 · Modelo 2: regressão logística para picos por CEP** — *principal* · `etapas/B07_modelo2_picos_logistica.py`  
  Regressão logística (log(1+x), padronização, C=0,3, pesos balanceados) com camadas de informação: só o CEP, + vizinhança, + cidade até ontem, + quedas na cidade no dia (referência). Mede AUC e quantos picos caem nos 0,1%, 1%, 5% e 10% de maior risco.  
  Lê: código de B06_modelo2_picos_gbm.py. Grava: model_lr.json.  
  Usado em: Documento de aprendizado de máquina; página de picos.
- **B08 · Como começam os temporais** — *principal* · `etapas/B08_temporais_na_cidade.py`  
  Para cada temporal (40+ quedas), mostra o comportamento da cidade nos dias anteriores e a hora em que se chega a 10 quedas.  
  Lê: ev.pkl, full.pkl, mats.npz. Grava: city.json.  
  Usado em: Página de picos.
- **B09 · Dados da página "Picos de chamados por CEP"** — *principal* · `etapas/B09_dados_pagina_picos.py`  
  Reúne os resultados anteriores num JSON para a página.  
  Lê: cepday.pkl, city.json, ev.pkl, full.pkl, mats.npz, model_lr.json, prof.json, selfctl.json, vol.pkl. Grava: data.json.  
  Usado em: Página de picos.

### C — Clima
- **C01 · Clima × quedas na cidade** — *principal* · `etapas/C01_clima_e_quedas_na_cidade.py`  
  Junta o clima diário às quedas por dia e mede quanto cada variável de clima separa os dias de temporal (AUC).  
  Lê: clima.pkl, mats.npz. Grava: cityday.pkl.  
  Usado em: Página de picos; base de C02.
- **C02 · Regra de alerta de chuva e vento** — *principal* · `etapas/C02_alerta_de_chuva_e_vento.py`  
  Testa limites simples (rajada ≥ 60 km/h, chuva ≥ 15 mm no dia ou ≥ 8 mm em 1 hora, no dia ou na véspera) para marcar dias de alerta.  
  Lê: cityday.pkl, clima.pkl. Grava: cityday2.pkl.  
  Usado em: Prontidão (F) e página de picos.
- **C03 · Modelo 2 com clima** — *principal* · `etapas/C03_modelo2_com_clima.py`  
  Acrescenta o clima do dia (como se a previsão fosse perfeita) e o da véspera ao modelo 2.  
  Lê: clima.pkl, código de B06_modelo2_picos_gbm.py. Grava: model_clima.json.  
  Usado em: Documento de aprendizado de máquina.
- **C04 · Preparo comum do modelo 2 com clima** — *biblioteca* · `etapas/C04_modelo2_preparo_clima.py`  
  Mesmo preparo de C03, sem treinar; usado por C05.  
  Lê: clima.pkl, código de B06_modelo2_picos_gbm.py. Grava: nada (só imprime).  
  Usado em: C05.
- **C05 · Modelo 2 com alerta × histórico** — *teste descartado* · `etapas/C05_modelo2_alerta_interacao.py`  
  Testa variáveis de interação entre o alerta de clima e o histórico do CEP. Não melhorou.  
  Lê: model_clima.json, código de C04_modelo2_preparo_clima.py. Grava: model_clima.json.  
  Usado em: Comparação.

### D — Em quanto tempo um pedido vira emergência
- **D01 · Pedidos seguidos de queda a até 30 e 100 m** — *principal* · `etapas/D01_pedidos_e_quedas_proximas.py`  
  Para cada pedido (poda, risco, remoção), procura a primeira árvore caída a até 30 m e 100 m depois dele.  
  Lê: full.pkl. Grava: P_lag.pkl, Q.pkl.  
  Usado em: Pergunta "em quanto tempo um pedido vira emergência".
- **D02 · Quedas por mês depois do pedido × data sorteada** — *exploratório* · `etapas/D02_risco_de_queda_por_mes.py`  
  Taxa de quedas próximas por mês depois do pedido, comparada com datas sorteadas (placebo).  
  Lê: P_lag.pkl, Q.pkl. Grava: q1_hz.pkl.  
  Usado em: Exploração para D03.
- **D03 · Quantas quedas tiveram pedido antes, e quanto antes** — *principal* · `etapas/D03_quedas_e_pedidos_anteriores.py`  
  Olha cada queda e procura pedidos a até 30 m no ano anterior; compara a mesma posição um ano antes (controle sazonal).  
  Lê: P_lag.pkl, Q.pkl. Grava: q1_hz2.pkl, q1_queda.pkl.  
  Usado em: Mesma pergunta.
- **D04 · Separando pedidos feitos perto de temporais** — *principal* · `etapas/D04_dias_calmos_e_temporais.py`  
  Repete a comparação separando pedidos de dias calmos e de perto de temporais.  
  Lê: P_lag.pkl, Q.pkl, mats.npz, q1_hz2.pkl. Grava: q1_hz2.pkl.  
  Usado em: Mesma pergunta.
- **D05 · Pedidos no CEP antes dos picos emergenciais** — *principal* · `etapas/D05_chamados_antes_dos_picos.py`  
  Fração dos picos com pedido não emergencial no CEP 3, 7, 30 e 90 dias antes, comparada com o ano anterior.  
  Lê: ev.pkl, mats.npz. Grava: nada (só imprime).  
  Usado em: Mesma pergunta.
- **D06 · Resumo para a página** — *principal* · `etapas/D06_resumo_tempo_ate_emergencia.py`  
  Junta os resultados de D01–D05 num JSON. Os números "pico" foram copiados da saída de D05.  
  Lê: P_lag.pkl, Q.pkl, q1_hz2.pkl. Grava: q1_out.json.  
  Usado em: Página de picos.

### E — Dado um temporal, onde caem as árvores
- **E01 · Dias de queda por quadrado de 1 km** — *principal* · `etapas/E01_quadrados_em_dias_de_queda.py`  
  Monta, para cada dia com 20+ quedas, as variáveis de cada quadrado de 1 km (histórico, pedidos recentes, chuva das estações próximas).  
  Lê: estacoes_diario.pkl, full.pkl. Grava: q2_rows.pkl.  
  Usado em: Pergunta "dado um temporal, onde caem as árvores".
- **E02 · Quanto cada informação acerta onde caem** — *principal* · `etapas/E02_avaliar_onde_caem.py`  
  Compara listas de quadrados (histórico, pedidos recentes, chuva local, modelos de Poisson) pela fração das quedas capturadas.  
  Lê: q2_rows.pkl. Grava: q2_summ.json.  
  Usado em: Mesma pergunta.
- **E03 · Mapa de cada temporal** — *principal* · `etapas/E03_mapa_por_temporal.py`  
  Para cada temporal, guarda as quedas, os quadrados apontados pelo histórico e a chuva das estações.  
  Lê: estacoes_diario.pkl, full.pkl, q2_rows.pkl. Grava: q2_map.json.  
  Usado em: Página de picos.
- **E04 · Atualizar a lista com as primeiras quedas do dia** — *principal* · `etapas/E04_atualizar_durante_o_dia.py`  
  Mede quanto melhora a lista quando se usam as primeiras quedas registradas no dia e os quadrados vizinhos.  
  Lê: full.pkl, q2_rows.pkl. Grava: q2_now.json.  
  Usado em: Mesma pergunta.

### F — Prontidão em dias de temporal (modelo 3)
- **F01 · Matrizes quadrado × dia** — *principal* · `etapas/F01_matrizes_quadrado_dia.py`  
  Conta, para cada quadrado de 1 km e dia, todos os chamados, as quedas, os pedidos e os pedidos ainda abertos.  
  Lê: full.pkl, q2_rows.pkl. Grava: q7mats.npz.  
  Usado em: Modelo 3.
- **F02 · Modelo 3: regressão de Poisson para prontidão** — *principal* · `etapas/F02_modelo3_prontidao_poisson.py`  
  Regressão de Poisson por quadrado-dia com camadas (mapa fixo, pedidos recentes, cidade ontem, clima do dia com interações) e gradient boosting para comparação. Mede a fração das quedas capturada com 0,5% a 10% dos quadrados-dia em alerta.  
  Lê: clima.pkl, q7mats.npz. Grava: q7_pred.pkl, q7_res.json.  
  Usado em: Documento de aprendizado de máquina; página de picos.
- **F03 · Regra de bolso de prontidão** — *principal* · `etapas/F03_regra_de_bolso_alerta.py`  
  Testa a regra "10 quadrados em dias normais, 200 em dias de alerta" e resume por dia.  
  Lê: cityday2.pkl, q7_pred.pkl. Grava: q7_days.pkl.  
  Usado em: Página de picos.
- **F04 · Exemplos de dias para a página** — *principal* · `etapas/F04_exemplos_de_dias.py`  
  Separa exemplos de dias com os quadrados em alerta e as quedas reais.  
  Lê: cityday2.pkl, full.pkl, q2_rows.pkl, q7_days.pkl, q7_pred.pkl, q7_res.json. Grava: q7_out.json.  
  Usado em: Página de picos.

### G — Cobertura de árvores
- **G01 · Setores censitários em dias de queda** — *principal* · `etapas/G01_setores_em_dias_de_queda.py`  
  Monta matrizes por setor censitário e as variáveis de árvore e ocupação de cada setor.  
  Lê: full.pkl, setor censitário (dados_entrada). Grava: t1_mats.npz, t1_rows.pkl.  
  Usado em: Pergunta sobre cobertura de árvores.
- **G02 · A cobertura de árvores ajuda a prever onde caem?** — *principal* · `etapas/G02_arvores_ajudam_a_prever.py`  
  Compara listas de setores: só árvore, só histórico, histórico + árvore.  
  Lê: t1_rows.pkl. Grava: t2_res.json.  
  Usado em: Mesma pergunta.
- **G03 · Setores que pedem menos do que o esperado** — *principal* · `etapas/G03_quem_liga_menos.py`  
  Estima quantos pedidos cada setor "deveria" ter pela árvore e ocupação e compara quedas por pedido entre quem liga menos e quem liga mais.  
  Lê: t1_mats.npz, setor censitário (dados_entrada). Grava: t3_bairro.json, t3_terc.json.  
  Usado em: Viés de sub-notificação (limites).

### H — Árvores e rede elétrica: trechos e modelo 1
- **H01 · Trechos de rua e volta do problema depois da poda** — *principal* · `etapas/H01_trechos_e_rebrota.py`  
  Cria o trecho (logradouro + faixa de 100 números), mede quantos pedidos da Light surgem onde já havia outro e, depois de uma poda atendida, em quanto tempo o trecho volta a ter qualquer pedido ou pedido que depende da Light (curvas de Kaplan–Meier).  
  Lê: P.pkl. Grava: Ptr.pkl, c2.json, surv.pkl.  
  Usado em: Página "Árvores e rede elétrica"; base do modelo 1.
- **H02 · Modelo 1: variáveis e alvo por trecho** — *principal* · `etapas/H02_modelo1_dados.py`  
  Calcula as 22 variáveis de cada trecho em uma data (histórico de poda, pendências, tempos, vizinhos, rua, árvore e construção do setor) e o alvo (novo Pendente em 12 meses). Datas: treino jul/2023 e jan/2024; teste jan/2025 e jul/2025.  
  Lê: Ptr.pkl, df.pkl, setor censitário (dados_entrada). Grava: m_data.pkl.  
  Usado em: Modelo 1; ranking.
- **H03 · Modelo 1: treino e avaliação** — *principal* · `etapas/H03_modelo1_treino_avaliacao.py`  
  Treina o gradient boosting (400 árvores, taxa 0,04, 31 folhas, 40 por folha, L2=1) e mede precisão no topo, AUC, calibração e importância por permutação, comparando com regras simples.  
  Lê: m_data.pkl. Grava: gb.pkl, m_res.json.  
  Usado em: Documento de aprendizado de máquina; página Light.
- **H04 · Acerto por escala (trecho, 500 números, rua)** — *principal* · `etapas/H04_precisao_por_escala.py`  
  Repete a regra "mais pendentes" em trechos de 100, 300 e 500 números e na rua inteira.  
  Lê: df.pkl. Grava: m3_res.json.  
  Usado em: Página Light.
- **H05 · Acerto das listas por escala, vazamento, sorteio e estoque** — *principal* · `etapas/H05_acerto_por_escala_e_vazamento.py`  
  Refaz as listas "mais pendentes" (trecho, 500 números, rua; 12 e 18 meses) contando como pendente só pedidos com 60 ou 180 dias na data de corte, para medir o efeito de usar o status de hoje. Calcula também o acerto de uma lista sorteada e quanto dos novos pedidos de 2025 caiu nos trechos que já esperavam.  
  Lê: P.pkl, df.pkl. Grava: b3.json, base.json, leak.json.  
  Usado em: Página Light; limites.
- **H06 · Lista de 500 trechos prioritários** — *principal* · `etapas/H06_lista_trechos_prioritarios.py`  
  Aplica o modelo 1 aos dados atuais e gera a lista de trechos com mais pedidos esperando a Light.  
  Lê: gb.pkl, código de H02_modelo1_dados.py. Grava: L.pkl, lista_prioridade_trechos_light.csv, pilot.json.  
  Usado em: Planilha lista_prioridade_trechos_light.csv.
- **H07 · Série mensal de pedidos que dependem da Light** — *principal* · `etapas/H07_serie_mensal_light.py`  
  Pedidos de poda e Pendentes por mês e por ano.  
  Lê: df.pkl. Grava: b2.json.  
  Usado em: Sazonalidade.
- **H08 · Como os pedidos longos são fechados hoje** — *principal* · `etapas/H08_pratica_atual_fechamentos.py`  
  Pedidos atendidos depois de mais de 1 ano: quantos fecham sozinhos e quantos junto com vizinhos no mesmo dia.  
  Lê: P.pkl. Grava: nada (só imprime).  
  Usado em: Página Light.
- **H09 · O fechamento em massa de outubro de 2025** — *principal* · `etapas/H09_fechamento_em_massa.py`  
  Descreve os 4 mil pedidos fechados em 13–14/10/2025.  
  Lê: P.pkl. Grava: nada (só imprime).  
  Usado em: Limites.
- **H10 · Repetição incluindo os fechados em massa** — *principal* · `etapas/H10_repeticao_com_fechados_em_massa.py`  
  Refaz a taxa de repetição tratando os fechados em massa como Pendentes.  
  Lê: df.pkl. Grava: nada (só imprime).  
  Usado em: Limites.

### I — Frentes de desligamento
- **I01 · Funções de agrupamento em frentes** — *biblioteca* · `etapas/I01_janelas_biblioteca.py`  
  Funções usadas por I06 e I07: estoque de pedidos por trecho numa data e agrupamento guloso por raio.  
  Lê: df.pkl. Grava: nada (só imprime).  
  Usado em: I06, I07.
- **I02 · Frentes por componentes conexos** — *exploratório* · `etapas/I02_frentes_conexas.py`  
  Primeira versão das frentes: trechos ligados por distância.  
  Lê: df.pkl. Grava: backlog_now.pkl, jan.json, janelas_now.pkl.  
  Usado em: Exploração.
- **I03 · Frentes pelo algoritmo guloso** — *principal* · `etapas/I03_frentes_algoritmo_guloso.py`  
  Agrupa o estoque de pedidos em frentes: pega o trecho com mais pedidos num raio, forma a frente, retira e repete.  
  Lê: jan.json, código de I02_frentes_conexas.py. Grava: backlog_now.pkl, jan.json, janelas_now.pkl.  
  Usado em: Página Light; painel do piloto.
- **I04 · Sazonalidade e clima dos pedidos da Light** — *principal* · `etapas/I04_sazonalidade_e_clima_light.py`  
  Pedidos que dependem da Light por mês do ano e em dias de alerta de clima.  
  Lê: P.pkl, clima.pkl. Grava: n1.json.  
  Usado em: Página Light.
- **I05 · Árvores, construção e pedidos da Light por setor** — *principal* · `etapas/I05_arvores_e_construcao_light.py`  
  Pedidos da Light por 1.000 habitantes conforme cobertura de árvores e área construída do setor.  
  Lê: P.pkl, setor censitário (dados_entrada). Grava: n2.json.  
  Usado em: Página Light.
- **I06 · Frentes do estoque atual e poda dos vizinhos** — *principal* · `etapas/I06_frentes_estoque_atual_e_vizinhos.py`  
  Número de desligamentos por raio (50 a 300 m) e quanto da demanda de 2025 as frentes cobrem incluindo vizinhos a até 150 m.  
  Lê: código de I01_janelas_biblioteca.py. Grava: n3.json.  
  Usado em: Página Light; documento.
- **I07 · Vizinhos: pedidos da Light × controle** — *principal* · `etapas/I07_vizinhos_controle.py`  
  Compara a fração de novos pedidos perto do estoque entre pedidos da Light e pedidos comuns de poda.  
  Lê: código de I01_janelas_biblioteca.py. Grava: nada (só imprime).  
  Usado em: Página Light.

### J — Ranking "Onde podar agora"
- **J01 · Ranking: previsão do modelo 1 hoje** — *principal* · `etapas/J01_prob_modelo_por_trecho_hoje.py`  
  Aplica o modelo 1 em 21/09/2026 e associa cada trecho ao seu CEP.  
  Lê: gb.pkl, código de H02_modelo1_dados.py. Grava: prob_now.pkl.  
  Usado em: Sinal "previsão" da nota.
- **J02 · Ranking: sinais por CEP** — *principal* · `etapas/J02_sinais_por_cep.py`  
  Calcula por CEP: poda aberta na COMLURB (até 2 anos), pedidos Pendentes, chamados de risco e queda em 12 meses, espera e maior previsão do modelo.  
  Lê: df.pkl, prob_now.pkl. Grava: cepg.pkl.  
  Usado em: Nota por CEP.
- **J03 · Ranking: nota por CEP** — *principal* · `etapas/J03_nota_por_cep.py`  
  Transforma cada sinal em 0–1 (escala log) e soma com os pesos 25/15/40/10/10.  
  Lê: cepg.pkl, df.pkl. Grava: cep_rank.pkl.  
  Usado em: Página "Onde podar agora".
- **J04 · Ranking: planilha e dados da página** — *principal* · `etapas/J04_csv_e_dados_da_pagina.py`  
  Gera ranking_ceps_poda.csv (com posição na zona e ação sugerida) e o JSON usado pela página.  
  Lê: P.pkl, cep_rank.pkl, df.pkl. Grava: rank_data.json, ranking_ceps_poda.csv.  
  Usado em: Planilha e página.
- **J05 · Validação da primeira versão da nota** — *exploratório* · `etapas/J05_validacao_inicial_ranking.py`  
  Teste de 2025 da nota com os pesos antigos e o status de hoje (versão superada por J07–J13).  
  Lê: df.pkl, gb.pkl, código de H02_modelo1_dados.py. Grava: nada (só imprime).  
  Usado em: Histórico.
- **J06 · Diagnóstico: justificativas, zonas e fechamento em massa** — *principal* · `etapas/J06_diagnostico_justificativas_zonas.py`  
  Motivos de fechamento sem atendimento, perfil de registro por zona e ano, repetição após cada tipo de fechamento e teste dos pedidos fechados em massa.  
  Lê: P.pkl, df.pkl. Grava: nada (só imprime).  
  Usado em: Limites; decisão de não incluir fechados em massa.
- **J07 · Sinais por CEP em datas passadas** — *principal* · `etapas/J07_sinais_em_varias_datas.py`  
  Reconstrói os sinais por CEP em jul/2024, jan/2025, jul/2025 e hoje, sabendo quais pedidos estavam abertos em cada data, mais sinais extras testados (vizinhança, quedas no quadrado, árvore, endereços) e o que aconteceu nos 12 meses seguintes.  
  Lê: df.pkl, gb.pkl, código de H02_modelo1_dados.py, setor censitário (dados_entrada). Grava: pri_feats.pkl.  
  Usado em: Melhoria da nota.
- **J08 · Quanto cada sinal acerta sozinho** — *principal* · `etapas/J08_avaliar_sinais.py`  
  Acerto de cada sinal e da nota atual nos 200, 500 e 1.000 CEPs do topo.  
  Lê: pri_feats.pkl. Grava: pri_comps.pkl.  
  Usado em: Melhoria da nota.
- **J09 · Busca dos pesos** — *principal* · `etapas/J09_otimizar_pesos.py`  
  Busca local de pesos (passos de 5 pontos) que maximiza o acerto médio; treina em 2024 e testa em 2025.  
  Lê: código de J08_avaliar_sinais.py. Grava: pri_opt.pkl.  
  Usado em: Escolha dos pesos 25/15/40/10/10.
- **J10 · Modelo de aprendizado de máquina no lugar da soma** — *teste descartado* · `etapas/J10_comparar_com_gbm.py`  
  Gradient boosting no nível do CEP. Ganhou pouco e de forma instável.  
  Lê: código de J08_avaliar_sinais.py. Grava: nada (só imprime).  
  Usado em: Comparação.
- **J11 · Sinais em 8 datas, com modelo retreinado** — *principal* · `etapas/J11_dados_8_cortes.py`  
  Reconstrói os sinais em 8 datas trimestrais (jan/2024 a set/2025), retreinando o modelo 1 em cada uma só com o passado.  
  Lê: df.pkl, gb.pkl, código de H02_modelo1_dados.py, setor censitário (dados_entrada). Grava: pri_roll.pkl.  
  Usado em: Robustez dos pesos; nota como chance.
- **J12 · Robustez dos pesos** — *principal* · `etapas/J12_robustez_dos_pesos.py`  
  Ótimo por período, 3.000 combinações sorteadas, ótimo conjunto, teste rolante, curva do peso da Light, metas alternativas e bootstrap.  
  Lê: pri_roll.pkl. Grava: pri_rob.pkl.  
  Usado em: Página: "Os pesos valem em outros períodos?".
- **J13 · Deixar um período de fora** — *principal* · `etapas/J13_deixar_um_periodo_de_fora.py`  
  Otimiza com 7 períodos e testa no oitavo, para cada período.  
  Lê: código de J12_robustez_dos_pesos.py. Grava: nada (só imprime).  
  Usado em: Decisão de manter os pesos.
- **J14 · Nota como chance** — *principal* · `etapas/J14_nota_como_chance.py`  
  Curva logística da nota para chance de árvore caída e de novo pedido na fiação (8 datas).  
  Lê: df.pkl, pri_roll.pkl. Grava: ifnot.pkl.  
  Usado em: Página: "Se não podar".
- **J15 · Atender a tempo reduz as quedas?** — *principal* · `etapas/J15_atendido_vs_nao_atendido.py`  
  Compara, na mesma faixa de nota, lugares onde a maior parte dos pedidos foi atendida em até 3 meses com lugares sem atendimento.  
  Lê: df.pkl, pri_roll.pkl. Grava: nada (só imprime).  
  Usado em: Página: "Atender a tempo reduz as quedas".
- **J16 · Mapa de risco** — *principal* · `etapas/J16_mapa_de_risco.py`  
  Quedas de dezembro a abril por quadrado de 1 km e teste no verão 2025–26.  
  Lê: df.pkl, full.pkl. Grava: cell_quedas.json.  
  Usado em: Página: mapa de risco.
- **J17 · Números fixos da página** — *principal* · `etapas/J17_numeros_da_pagina.py`  
  Tabela de validação, faixas de nota e gráfico de robustez.  
  Lê: pri_feats.pkl, pri_rob.pkl, pri_roll.pkl. Grava: bands8.json, pri_page.json, rob_rows.json.  
  Usado em: Página.
- **J18 · Montar a página e o site** — *principal* · `etapas/J18_montar_pagina.py`  
  Insere o ranking e o mapa no modelo HTML e gera a versão do artefato e o index.html do GitHub Pages.  
  Lê: cell_quedas.json. Grava: nada (só imprime).  
  Usado em: Página e site.

## Conferência

O pacote foi rodado do zero em 13/10/2026, a partir dos CSVs originais, numa pasta nova, e os resultados foram comparados com os da análise:

- **31 dos 33 arquivos de resultado (`.json`) são idênticos.** Os outros dois diferem só por campos acrescentados à mão na análise original, depois que as etapas rodaram: `data.json` ganhou o clima de cada temporal e `pri_page.json` uma tabela de faixas que não é mais usada.
- **A planilha `ranking_ceps_poda.csv`, a lista `lista_prioridade_trechos_light.csv`, o mapa de quedas e a página `index.html` são idênticos** aos publicados.
- Não são gerados aqui os pacotes de dados das páginas antigas (`data2.json`, `ldata.json`, `ndata.json`, `painel.json`). Eles só reuniam, para cada página, números que as etapas acima já calculam.
