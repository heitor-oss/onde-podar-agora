# Todas as etapas, uma a uma

Voltar para o [guia do código](README.md).

Tipos: **principal** (gera resultado usado nas páginas ou documentos), **exploratório** (passo intermediário da análise), **teste descartado** (alternativa testada e abandonada) e **biblioteca** (código reaproveitado por outras etapas; não roda sozinho).


## A — Preparação dos dados

### [A01 · Juntar as 4 partes dos chamados do 1746](etapas/A01_juntar_chamados.py)
*principal*

Lê os quatro CSVs de chamados (com CEP já atribuído), junta numa tabela só e cria a coluna d (dia do chamado).

- **Lê:** 4 partes dos chamados (dados_entrada)
- **Grava:** full.pkl
- **Usado em:** Base de todas as análises.

### [A02 · Base de poda com datas, bairros, RAs e zonas](etapas/A02_base_poda_bairros_zonas.py)
*principal*

Converte datas de abertura e fechamento, calcula a duração (pedidos abertos contam até 20/09/2026), traz bairro e região administrativa pelo setor censitário, separa os pedidos de poda e marca pend = status Pendente (aproximação de "depende da Light"). Classifica a zona da cidade pela RA; RA desconhecida entra como Norte.

- **Lê:** full.pkl, setor censitário (dados_entrada)
- **Grava:** P.pkl, df.pkl
- **Usado em:** Todas as análises de poda e Light; ranking.

### [A03 · Clima diário da cidade (Open-Meteo)](etapas/A03_clima_openmeteo.py)
*principal*

Lê o clima diário (chuva média, chuva máxima, maior chuva em 1 hora, maior rajada, chuva dos 3 e 7 dias anteriores) e confere as somas.

- **Lê:** clima Open-Meteo (dados_entrada)
- **Grava:** clima.pkl
- **Usado em:** Modelos 2 e 3, sazonalidade.

### [A04 · Pluviômetros do Alerta Rio e WebSirene (Data.Rio)](etapas/A04_clima_estacoes.py)
*principal*

Lê os arquivos diários dos pluviômetros baixados do BigQuery do Data.Rio (notebook em notebooks/), filtra dias com registros suficientes e junta com as coordenadas das estações.

- **Lê:** pluviômetros Data.Rio (dados_entrada)
- **Grava:** estacoes.pkl, estacoes_diario.pkl
- **Usado em:** Pergunta "dado um temporal, onde caem as árvores" (E).


## B — Picos de chamados por CEP

### [B01 · Exploração: dias de pico na cidade](etapas/B01_explorar_picos_da_cidade.py)
*exploratório*

Compara o total de chamados de cada dia com a mediana das 4 semanas anteriores e lista os maiores dias de quedas.

- **Lê:** full.pkl
- **Grava:** nada (só imprime)
- **Usado em:** Primeira exploração; não gera arquivo.

### [B02 · Exploração: quantos endereços por CEP-dia](etapas/B02_explorar_pontos_por_cep_dia.py)
*exploratório*

Conta, para cada CEP e dia, quantos chamados e quantos pontos diferentes houve, para separar vários chamados sobre a mesma árvore de problemas espalhados.

- **Lê:** full.pkl
- **Grava:** nada (só imprime)
- **Usado em:** Definição de pico.

### [B03 · Tabela CEP × dia e matrizes de chamados](etapas/B03_tabela_cep_dia_e_matrizes.py)
*principal*

Monta matrizes CEP × dia com todos os chamados, as quedas e os pedidos de avaliação de risco, a tabela cepday (chamados, pontos, quedas, horário, bairro, rua) e marca os dias de temporal (40 ou mais quedas na cidade).

- **Lê:** full.pkl
- **Grava:** cepday.pkl, mats.npz, peaks.pkl
- **Usado em:** Picos por CEP, modelo 2, clima.

### [B04 · Picos por CEP e o que acontece antes deles](etapas/B04_eventos_e_perfil_antes_do_pico.py)
*principal*

Define pico emergencial (3+ chamados de queda ou risco em 2+ endereços no mesmo CEP e dia) e picos de volume (5+ chamados, "lote" no mesmo endereço ou "mutirão" na rua). Compara os chamados nos dias anteriores ao pico com CEPs sorteados.

- **Lê:** cepday.pkl, mats.npz
- **Grava:** ev.pkl, prof.json, vol.pkl
- **Usado em:** Página "Picos de chamados por CEP".

### [B05 · Antes do pico × o próprio CEP em outras épocas](etapas/B05_comparacao_com_o_proprio_cep.py)
*principal*

Compara os 30 dias antes de cada pico com janelas sorteadas do mesmo CEP longe do pico.

- **Lê:** ev.pkl, mats.npz, vol.pkl
- **Grava:** selfctl.json
- **Usado em:** Página "Picos de chamados por CEP".

### [B06 · Modelo 2 com gradient boosting (descartado)](etapas/B06_modelo2_picos_gbm.py)
*teste descartado*

Treina gradient boosting para prever picos por CEP-dia com amostragem de dias sem pico. Com só 57 picos no treino, decorou os exemplos e foi pior que a regressão logística. Define as variáveis usadas pelos passos seguintes.

- **Lê:** ev.pkl, mats.npz, vol.pkl
- **Grava:** model.json
- **Usado em:** Comparação; base de B07 e C03.

### [B07 · Modelo 2: regressão logística para picos por CEP](etapas/B07_modelo2_picos_logistica.py)
*principal*

Regressão logística (log(1+x), padronização, C=0,3, pesos balanceados) com camadas de informação: só o CEP, + vizinhança, + cidade até ontem, + quedas na cidade no dia (referência). Mede AUC e quantos picos caem nos 0,1%, 1%, 5% e 10% de maior risco.

- **Lê:** código de B06_modelo2_picos_gbm.py
- **Grava:** model_lr.json
- **Usado em:** Documento de aprendizado de máquina; página de picos.

### [B08 · Como começam os temporais](etapas/B08_temporais_na_cidade.py)
*principal*

Para cada temporal (40+ quedas), mostra o comportamento da cidade nos dias anteriores e a hora em que se chega a 10 quedas.

- **Lê:** ev.pkl, full.pkl, mats.npz
- **Grava:** city.json
- **Usado em:** Página de picos.

### [B09 · Dados da página "Picos de chamados por CEP"](etapas/B09_dados_pagina_picos.py)
*principal*

Reúne os resultados anteriores num JSON para a página.

- **Lê:** cepday.pkl, city.json, ev.pkl, full.pkl, mats.npz, model_lr.json, prof.json, selfctl.json, vol.pkl
- **Grava:** data.json
- **Usado em:** Página de picos.


## C — Clima

### [C01 · Clima × quedas na cidade](etapas/C01_clima_e_quedas_na_cidade.py)
*principal*

Junta o clima diário às quedas por dia e mede quanto cada variável de clima separa os dias de temporal (AUC).

- **Lê:** clima.pkl, mats.npz
- **Grava:** cityday.pkl
- **Usado em:** Página de picos; base de C02.

### [C02 · Regra de alerta de chuva e vento](etapas/C02_alerta_de_chuva_e_vento.py)
*principal*

Testa limites simples (rajada ≥ 60 km/h, chuva ≥ 15 mm no dia ou ≥ 8 mm em 1 hora, no dia ou na véspera) para marcar dias de alerta.

- **Lê:** cityday.pkl, clima.pkl
- **Grava:** cityday2.pkl
- **Usado em:** Prontidão (F) e página de picos.

### [C03 · Modelo 2 com clima](etapas/C03_modelo2_com_clima.py)
*principal*

Acrescenta o clima do dia (como se a previsão fosse perfeita) e o da véspera ao modelo 2.

- **Lê:** clima.pkl, código de B06_modelo2_picos_gbm.py
- **Grava:** model_clima.json
- **Usado em:** Documento de aprendizado de máquina.

### [C04 · Preparo comum do modelo 2 com clima](etapas/C04_modelo2_preparo_clima.py)
*biblioteca*

Mesmo preparo de C03, sem treinar; usado por C05.

- **Lê:** clima.pkl, código de B06_modelo2_picos_gbm.py
- **Grava:** nada (só imprime)
- **Usado em:** C05.

### [C05 · Modelo 2 com alerta × histórico](etapas/C05_modelo2_alerta_interacao.py)
*teste descartado*

Testa variáveis de interação entre o alerta de clima e o histórico do CEP. Não melhorou.

- **Lê:** model_clima.json, código de C04_modelo2_preparo_clima.py
- **Grava:** model_clima.json
- **Usado em:** Comparação.


## D — Em quanto tempo um pedido vira emergência

### [D01 · Pedidos seguidos de queda a até 30 e 100 m](etapas/D01_pedidos_e_quedas_proximas.py)
*principal*

Para cada pedido (poda, risco, remoção), procura a primeira árvore caída a até 30 m e 100 m depois dele.

- **Lê:** full.pkl
- **Grava:** P_lag.pkl, Q.pkl
- **Usado em:** Pergunta "em quanto tempo um pedido vira emergência".

### [D02 · Quedas por mês depois do pedido × data sorteada](etapas/D02_risco_de_queda_por_mes.py)
*exploratório*

Taxa de quedas próximas por mês depois do pedido, comparada com datas sorteadas (placebo).

- **Lê:** P_lag.pkl, Q.pkl
- **Grava:** q1_hz.pkl
- **Usado em:** Exploração para D03.

### [D03 · Quantas quedas tiveram pedido antes, e quanto antes](etapas/D03_quedas_e_pedidos_anteriores.py)
*principal*

Olha cada queda e procura pedidos a até 30 m no ano anterior; compara a mesma posição um ano antes (controle sazonal).

- **Lê:** P_lag.pkl, Q.pkl
- **Grava:** q1_hz2.pkl, q1_queda.pkl
- **Usado em:** Mesma pergunta.

### [D04 · Separando pedidos feitos perto de temporais](etapas/D04_dias_calmos_e_temporais.py)
*principal*

Repete a comparação separando pedidos de dias calmos e de perto de temporais.

- **Lê:** P_lag.pkl, Q.pkl, mats.npz, q1_hz2.pkl
- **Grava:** q1_hz2.pkl
- **Usado em:** Mesma pergunta.

### [D05 · Pedidos no CEP antes dos picos emergenciais](etapas/D05_chamados_antes_dos_picos.py)
*principal*

Fração dos picos com pedido não emergencial no CEP 3, 7, 30 e 90 dias antes, comparada com o ano anterior.

- **Lê:** ev.pkl, mats.npz
- **Grava:** nada (só imprime)
- **Usado em:** Mesma pergunta.

### [D06 · Resumo para a página](etapas/D06_resumo_tempo_ate_emergencia.py)
*principal*

Junta os resultados de D01–D05 num JSON. Os números "pico" foram copiados da saída de D05.

- **Lê:** P_lag.pkl, Q.pkl, q1_hz2.pkl
- **Grava:** q1_out.json
- **Usado em:** Página de picos.


## E — Dado um temporal, onde caem as árvores

### [E01 · Dias de queda por quadrado de 1 km](etapas/E01_quadrados_em_dias_de_queda.py)
*principal*

Monta, para cada dia com 20+ quedas, as variáveis de cada quadrado de 1 km (histórico, pedidos recentes, chuva das estações próximas).

- **Lê:** estacoes_diario.pkl, full.pkl
- **Grava:** q2_rows.pkl
- **Usado em:** Pergunta "dado um temporal, onde caem as árvores".

### [E02 · Quanto cada informação acerta onde caem](etapas/E02_avaliar_onde_caem.py)
*principal*

Compara listas de quadrados (histórico, pedidos recentes, chuva local, modelos de Poisson) pela fração das quedas capturadas.

- **Lê:** q2_rows.pkl
- **Grava:** q2_summ.json
- **Usado em:** Mesma pergunta.

### [E03 · Mapa de cada temporal](etapas/E03_mapa_por_temporal.py)
*principal*

Para cada temporal, guarda as quedas, os quadrados apontados pelo histórico e a chuva das estações.

- **Lê:** estacoes_diario.pkl, full.pkl, q2_rows.pkl
- **Grava:** q2_map.json
- **Usado em:** Página de picos.

### [E04 · Atualizar a lista com as primeiras quedas do dia](etapas/E04_atualizar_durante_o_dia.py)
*principal*

Mede quanto melhora a lista quando se usam as primeiras quedas registradas no dia e os quadrados vizinhos.

- **Lê:** full.pkl, q2_rows.pkl
- **Grava:** q2_now.json
- **Usado em:** Mesma pergunta.


## F — Prontidão em dias de temporal (modelo 3)

### [F01 · Matrizes quadrado × dia](etapas/F01_matrizes_quadrado_dia.py)
*principal*

Conta, para cada quadrado de 1 km e dia, todos os chamados, as quedas, os pedidos e os pedidos ainda abertos.

- **Lê:** full.pkl, q2_rows.pkl
- **Grava:** q7mats.npz
- **Usado em:** Modelo 3.

### [F02 · Modelo 3: regressão de Poisson para prontidão](etapas/F02_modelo3_prontidao_poisson.py)
*principal*

Regressão de Poisson por quadrado-dia com camadas (mapa fixo, pedidos recentes, cidade ontem, clima do dia com interações) e gradient boosting para comparação. Mede a fração das quedas capturada com 0,5% a 10% dos quadrados-dia em alerta.

- **Lê:** clima.pkl, q7mats.npz
- **Grava:** q7_pred.pkl, q7_res.json
- **Usado em:** Documento de aprendizado de máquina; página de picos.

### [F03 · Regra de bolso de prontidão](etapas/F03_regra_de_bolso_alerta.py)
*principal*

Testa a regra "10 quadrados em dias normais, 200 em dias de alerta" e resume por dia.

- **Lê:** cityday2.pkl, q7_pred.pkl
- **Grava:** q7_days.pkl
- **Usado em:** Página de picos.

### [F04 · Exemplos de dias para a página](etapas/F04_exemplos_de_dias.py)
*principal*

Separa exemplos de dias com os quadrados em alerta e as quedas reais.

- **Lê:** cityday2.pkl, full.pkl, q2_rows.pkl, q7_days.pkl, q7_pred.pkl, q7_res.json
- **Grava:** q7_out.json
- **Usado em:** Página de picos.


## G — Cobertura de árvores

### [G01 · Setores censitários em dias de queda](etapas/G01_setores_em_dias_de_queda.py)
*principal*

Monta matrizes por setor censitário e as variáveis de árvore e ocupação de cada setor.

- **Lê:** full.pkl, setor censitário (dados_entrada)
- **Grava:** t1_mats.npz, t1_rows.pkl
- **Usado em:** Pergunta sobre cobertura de árvores.

### [G02 · A cobertura de árvores ajuda a prever onde caem?](etapas/G02_arvores_ajudam_a_prever.py)
*principal*

Compara listas de setores: só árvore, só histórico, histórico + árvore.

- **Lê:** t1_rows.pkl
- **Grava:** t2_res.json
- **Usado em:** Mesma pergunta.

### [G03 · Setores que pedem menos do que o esperado](etapas/G03_quem_liga_menos.py)
*principal*

Estima quantos pedidos cada setor "deveria" ter pela árvore e ocupação e compara quedas por pedido entre quem liga menos e quem liga mais.

- **Lê:** t1_mats.npz, setor censitário (dados_entrada)
- **Grava:** t3_bairro.json, t3_terc.json
- **Usado em:** Viés de sub-notificação (limites).


## H — Árvores e rede elétrica: trechos e modelo 1

### [H01 · Trechos de rua e volta do problema depois da poda](etapas/H01_trechos_e_rebrota.py)
*principal*

Cria o trecho (logradouro + faixa de 100 números), mede quantos pedidos da Light surgem onde já havia outro e, depois de uma poda atendida, em quanto tempo o trecho volta a ter qualquer pedido ou pedido que depende da Light (curvas de Kaplan–Meier).

- **Lê:** P.pkl
- **Grava:** Ptr.pkl, c2.json, surv.pkl
- **Usado em:** Página "Árvores e rede elétrica"; base do modelo 1.

### [H02 · Modelo 1: variáveis e alvo por trecho](etapas/H02_modelo1_dados.py)
*principal*

Calcula as 22 variáveis de cada trecho em uma data (histórico de poda, pendências, tempos, vizinhos, rua, árvore e construção do setor) e o alvo (novo Pendente em 12 meses). Datas: treino jul/2023 e jan/2024; teste jan/2025 e jul/2025.

- **Lê:** Ptr.pkl, df.pkl, setor censitário (dados_entrada)
- **Grava:** m_data.pkl
- **Usado em:** Modelo 1; ranking.

### [H03 · Modelo 1: treino e avaliação](etapas/H03_modelo1_treino_avaliacao.py)
*principal*

Treina o gradient boosting (400 árvores, taxa 0,04, 31 folhas, 40 por folha, L2=1) e mede precisão no topo, AUC, calibração e importância por permutação, comparando com regras simples.

- **Lê:** m_data.pkl
- **Grava:** gb.pkl, m_res.json
- **Usado em:** Documento de aprendizado de máquina; página Light.

### [H04 · Acerto por escala (trecho, 500 números, rua)](etapas/H04_precisao_por_escala.py)
*principal*

Repete a regra "mais pendentes" em trechos de 100, 300 e 500 números e na rua inteira.

- **Lê:** df.pkl
- **Grava:** m3_res.json
- **Usado em:** Página Light.

### [H05 · Acerto das listas por escala, vazamento, sorteio e estoque](etapas/H05_acerto_por_escala_e_vazamento.py)
*principal*

Refaz as listas "mais pendentes" (trecho, 500 números, rua; 12 e 18 meses) contando como pendente só pedidos com 60 ou 180 dias na data de corte, para medir o efeito de usar o status de hoje. Calcula também o acerto de uma lista sorteada e quanto dos novos pedidos de 2025 caiu nos trechos que já esperavam.

- **Lê:** P.pkl, df.pkl
- **Grava:** b3.json, base.json, leak.json
- **Usado em:** Página Light; limites.

### [H06 · Lista de 500 trechos prioritários](etapas/H06_lista_trechos_prioritarios.py)
*principal*

Aplica o modelo 1 aos dados atuais e gera a lista de trechos com mais pedidos esperando a Light.

- **Lê:** gb.pkl, código de H02_modelo1_dados.py
- **Grava:** L.pkl, lista_prioridade_trechos_light.csv, pilot.json
- **Usado em:** Planilha lista_prioridade_trechos_light.csv.

### [H07 · Série mensal de pedidos que dependem da Light](etapas/H07_serie_mensal_light.py)
*principal*

Pedidos de poda e Pendentes por mês e por ano.

- **Lê:** df.pkl
- **Grava:** b2.json
- **Usado em:** Sazonalidade.

### [H08 · Como os pedidos longos são fechados hoje](etapas/H08_pratica_atual_fechamentos.py)
*principal*

Pedidos atendidos depois de mais de 1 ano: quantos fecham sozinhos e quantos junto com vizinhos no mesmo dia.

- **Lê:** P.pkl
- **Grava:** nada (só imprime)
- **Usado em:** Página Light.

### [H09 · O fechamento em massa de outubro de 2025](etapas/H09_fechamento_em_massa.py)
*principal*

Descreve os 4 mil pedidos fechados em 13–14/10/2025.

- **Lê:** P.pkl
- **Grava:** nada (só imprime)
- **Usado em:** Limites.

### [H10 · Repetição incluindo os fechados em massa](etapas/H10_repeticao_com_fechados_em_massa.py)
*principal*

Refaz a taxa de repetição tratando os fechados em massa como Pendentes.

- **Lê:** df.pkl
- **Grava:** nada (só imprime)
- **Usado em:** Limites.


## I — Frentes de desligamento

### [I01 · Funções de agrupamento em frentes](etapas/I01_janelas_biblioteca.py)
*biblioteca*

Funções usadas por I06 e I07: estoque de pedidos por trecho numa data e agrupamento guloso por raio.

- **Lê:** df.pkl
- **Grava:** nada (só imprime)
- **Usado em:** I06, I07.

### [I02 · Frentes por componentes conexos](etapas/I02_frentes_conexas.py)
*exploratório*

Primeira versão das frentes: trechos ligados por distância.

- **Lê:** df.pkl
- **Grava:** backlog_now.pkl, jan.json, janelas_now.pkl
- **Usado em:** Exploração.

### [I03 · Frentes pelo algoritmo guloso](etapas/I03_frentes_algoritmo_guloso.py)
*principal*

Agrupa o estoque de pedidos em frentes: pega o trecho com mais pedidos num raio, forma a frente, retira e repete.

- **Lê:** jan.json, código de I02_frentes_conexas.py
- **Grava:** backlog_now.pkl, jan.json, janelas_now.pkl
- **Usado em:** Página Light; painel do piloto.

### [I04 · Sazonalidade e clima dos pedidos da Light](etapas/I04_sazonalidade_e_clima_light.py)
*principal*

Pedidos que dependem da Light por mês do ano e em dias de alerta de clima.

- **Lê:** P.pkl, clima.pkl
- **Grava:** n1.json
- **Usado em:** Página Light.

### [I05 · Árvores, construção e pedidos da Light por setor](etapas/I05_arvores_e_construcao_light.py)
*principal*

Pedidos da Light por 1.000 habitantes conforme cobertura de árvores e área construída do setor.

- **Lê:** P.pkl, setor censitário (dados_entrada)
- **Grava:** n2.json
- **Usado em:** Página Light.

### [I06 · Frentes do estoque atual e poda dos vizinhos](etapas/I06_frentes_estoque_atual_e_vizinhos.py)
*principal*

Número de desligamentos por raio (50 a 300 m) e quanto da demanda de 2025 as frentes cobrem incluindo vizinhos a até 150 m.

- **Lê:** código de I01_janelas_biblioteca.py
- **Grava:** n3.json
- **Usado em:** Página Light; documento.

### [I07 · Vizinhos: pedidos da Light × controle](etapas/I07_vizinhos_controle.py)
*principal*

Compara a fração de novos pedidos perto do estoque entre pedidos da Light e pedidos comuns de poda.

- **Lê:** código de I01_janelas_biblioteca.py
- **Grava:** nada (só imprime)
- **Usado em:** Página Light.


## J — Ranking "Onde podar agora"

### [J01 · Ranking: previsão do modelo 1 hoje](etapas/J01_prob_modelo_por_trecho_hoje.py)
*principal*

Aplica o modelo 1 em 21/09/2026 e associa cada trecho ao seu CEP.

- **Lê:** gb.pkl, código de H02_modelo1_dados.py
- **Grava:** prob_now.pkl
- **Usado em:** Sinal "previsão" da nota.

### [J02 · Ranking: sinais por CEP](etapas/J02_sinais_por_cep.py)
*principal*

Calcula por CEP: poda aberta na COMLURB (até 2 anos), pedidos Pendentes, chamados de risco e queda em 12 meses, espera e maior previsão do modelo.

- **Lê:** df.pkl, prob_now.pkl
- **Grava:** cepg.pkl
- **Usado em:** Nota por CEP.

### [J03 · Ranking: nota por CEP](etapas/J03_nota_por_cep.py)
*principal*

Transforma cada sinal em 0–1 (escala log) e soma com os pesos 25/15/40/10/10.

- **Lê:** cepg.pkl, df.pkl
- **Grava:** cep_rank.pkl
- **Usado em:** Página "Onde podar agora".

### [J04 · Ranking: planilha e dados da página](etapas/J04_csv_e_dados_da_pagina.py)
*principal*

Gera ranking_ceps_poda.csv (com posição na zona e ação sugerida) e o JSON usado pela página.

- **Lê:** P.pkl, cep_rank.pkl, df.pkl
- **Grava:** rank_data.json, ranking_ceps_poda.csv
- **Usado em:** Planilha e página.

### [J05 · Validação da primeira versão da nota](etapas/J05_validacao_inicial_ranking.py)
*exploratório*

Teste de 2025 da nota com os pesos antigos e o status de hoje (versão superada por J07–J13).

- **Lê:** df.pkl, gb.pkl, código de H02_modelo1_dados.py
- **Grava:** nada (só imprime)
- **Usado em:** Histórico.

### [J06 · Diagnóstico: justificativas, zonas e fechamento em massa](etapas/J06_diagnostico_justificativas_zonas.py)
*principal*

Motivos de fechamento sem atendimento, perfil de registro por zona e ano, repetição após cada tipo de fechamento e teste dos pedidos fechados em massa.

- **Lê:** P.pkl, df.pkl
- **Grava:** nada (só imprime)
- **Usado em:** Limites; decisão de não incluir fechados em massa.

### [J07 · Sinais por CEP em datas passadas](etapas/J07_sinais_em_varias_datas.py)
*principal*

Reconstrói os sinais por CEP em jul/2024, jan/2025, jul/2025 e hoje, sabendo quais pedidos estavam abertos em cada data, mais sinais extras testados (vizinhança, quedas no quadrado, árvore, endereços) e o que aconteceu nos 12 meses seguintes.

- **Lê:** df.pkl, gb.pkl, código de H02_modelo1_dados.py, setor censitário (dados_entrada)
- **Grava:** pri_feats.pkl
- **Usado em:** Melhoria da nota.

### [J08 · Quanto cada sinal acerta sozinho](etapas/J08_avaliar_sinais.py)
*principal*

Acerto de cada sinal e da nota atual nos 200, 500 e 1.000 CEPs do topo.

- **Lê:** pri_feats.pkl
- **Grava:** pri_comps.pkl
- **Usado em:** Melhoria da nota.

### [J09 · Busca dos pesos](etapas/J09_otimizar_pesos.py)
*principal*

Busca local de pesos (passos de 5 pontos) que maximiza o acerto médio; treina em 2024 e testa em 2025.

- **Lê:** código de J08_avaliar_sinais.py
- **Grava:** pri_opt.pkl
- **Usado em:** Escolha dos pesos 25/15/40/10/10.

### [J10 · Modelo de aprendizado de máquina no lugar da soma](etapas/J10_comparar_com_gbm.py)
*teste descartado*

Gradient boosting no nível do CEP. Ganhou pouco e de forma instável.

- **Lê:** código de J08_avaliar_sinais.py
- **Grava:** nada (só imprime)
- **Usado em:** Comparação.

### [J11 · Sinais em 8 datas, com modelo retreinado](etapas/J11_dados_8_cortes.py)
*principal*

Reconstrói os sinais em 8 datas trimestrais (jan/2024 a set/2025), retreinando o modelo 1 em cada uma só com o passado.

- **Lê:** df.pkl, gb.pkl, código de H02_modelo1_dados.py, setor censitário (dados_entrada)
- **Grava:** pri_roll.pkl
- **Usado em:** Robustez dos pesos; nota como chance.

### [J12 · Robustez dos pesos](etapas/J12_robustez_dos_pesos.py)
*principal*

Ótimo por período, 3.000 combinações sorteadas, ótimo conjunto, teste rolante, curva do peso da Light, metas alternativas e bootstrap.

- **Lê:** pri_roll.pkl
- **Grava:** pri_rob.pkl
- **Usado em:** Página: "Os pesos valem em outros períodos?".

### [J13 · Deixar um período de fora](etapas/J13_deixar_um_periodo_de_fora.py)
*principal*

Otimiza com 7 períodos e testa no oitavo, para cada período.

- **Lê:** código de J12_robustez_dos_pesos.py
- **Grava:** nada (só imprime)
- **Usado em:** Decisão de manter os pesos.

### [J14 · Nota como chance](etapas/J14_nota_como_chance.py)
*principal*

Curva logística da nota para chance de árvore caída e de novo pedido na fiação (8 datas).

- **Lê:** df.pkl, pri_roll.pkl
- **Grava:** ifnot.pkl
- **Usado em:** Página: "Se não podar".

### [J15 · Atender a tempo reduz as quedas?](etapas/J15_atendido_vs_nao_atendido.py)
*principal*

Compara, na mesma faixa de nota, lugares onde a maior parte dos pedidos foi atendida em até 3 meses com lugares sem atendimento.

- **Lê:** df.pkl, pri_roll.pkl
- **Grava:** nada (só imprime)
- **Usado em:** Página: "Atender a tempo reduz as quedas".

### [J16 · Mapa de risco](etapas/J16_mapa_de_risco.py)
*principal*

Quedas de dezembro a abril por quadrado de 1 km e teste no verão 2025–26.

- **Lê:** df.pkl, full.pkl
- **Grava:** cell_quedas.json
- **Usado em:** Página: mapa de risco.

### [J17 · Números fixos da página](etapas/J17_numeros_da_pagina.py)
*principal*

Tabela de validação, faixas de nota e gráfico de robustez.

- **Lê:** pri_feats.pkl, pri_rob.pkl, pri_roll.pkl
- **Grava:** bands8.json, pri_page.json, rob_rows.json
- **Usado em:** Página.

### [J18 · Montar a página e o site](etapas/J18_montar_pagina.py)
*principal*

Insere o ranking e o mapa no modelo HTML e gera a versão do artefato e o index.html do GitHub Pages.

- **Lê:** cell_quedas.json
- **Grava:** nada (só imprime)
- **Usado em:** Página e site.
