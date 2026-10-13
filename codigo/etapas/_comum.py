"""
Configuração comum a todas as etapas: onde ficam os dados de entrada, os arquivos
intermediários e as saídas. Para usar outras pastas, defina as variáveis de ambiente
PODA_ENTRADA e PODA_TRABALHO antes de rodar.
"""
import os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # pasta codigo/
ETAPAS = os.path.join(RAIZ, 'etapas')
ENTRADA = os.environ.get('PODA_ENTRADA', os.path.join(RAIZ, 'dados_entrada'))  # arquivos de entrada
TRABALHO = os.environ.get('PODA_TRABALHO', os.path.join(RAIZ, 'trabalho'))     # intermediários (.pkl, .json, .npz)
SAIDAS = os.path.join(RAIZ, 'saidas')                                           # planilhas e páginas finais

SETOR = os.path.join(ENTRADA, 'dados_finais_setor_v3_subtipos1a9.csv')   # setores censitários (árvores, construção, bairro, RA)
CLIMA_OPENMETEO = os.path.join(ENTRADA, 'clima_diario_rio_openmeteo.csv') # clima diário da cidade
CLIMA_ESTACOES_ZIP = os.path.join(ENTRADA, 'clima_estacoes_rio.zip')      # pluviômetros (Data.Rio / BigQuery)

# Algumas etapas reaproveitam o código de outras (exec). Este mapa liga o nome
# original do script, usado nesses trechos, ao nome da etapa neste pacote.
ORIGEM = {
    "v1.py": "A02_base_poda_bairros_zonas.py",
    "q2prep.py": "A04_clima_estacoes.py",
    "a1.py": "B01_explorar_picos_da_cidade.py",
    "a2.py": "B02_explorar_pontos_por_cep_dia.py",
    "a3.py": "B03_tabela_cep_dia_e_matrizes.py",
    "a4.py": "B04_eventos_e_perfil_antes_do_pico.py",
    "a5.py": "B05_comparacao_com_o_proprio_cep.py",
    "a6.py": "B06_modelo2_picos_gbm.py",
    "a7.py": "B07_modelo2_picos_logistica.py",
    "a8.py": "B08_temporais_na_cidade.py",
    "a9.py": "B09_dados_pagina_picos.py",
    "w1.py": "C01_clima_e_quedas_na_cidade.py",
    "w2.py": "C02_alerta_de_chuva_e_vento.py",
    "w3.py": "C03_modelo2_com_clima.py",
    "w3_head.py": "C04_modelo2_preparo_clima.py",
    "w4.py": "C05_modelo2_alerta_interacao.py",
    "q1.py": "D01_pedidos_e_quedas_proximas.py",
    "q1b.py": "D02_risco_de_queda_por_mes.py",
    "q1c.py": "D03_quedas_e_pedidos_anteriores.py",
    "q1d.py": "D04_dias_calmos_e_temporais.py",
    "q1e.py": "D05_chamados_antes_dos_picos.py",
    "q1f.py": "D06_resumo_tempo_ate_emergencia.py",
    "q2.py": "E01_quadrados_em_dias_de_queda.py",
    "q2eval.py": "E02_avaliar_onde_caem.py",
    "q2map.py": "E03_mapa_por_temporal.py",
    "q2now.py": "E04_atualizar_durante_o_dia.py",
    "q7prep.py": "F01_matrizes_quadrado_dia.py",
    "q7.py": "F02_modelo3_prontidao_poisson.py",
    "q7b.py": "F03_regra_de_bolso_alerta.py",
    "q7c.py": "F04_exemplos_de_dias.py",
    "t1.py": "G01_setores_em_dias_de_queda.py",
    "t2.py": "G02_arvores_ajudam_a_prever.py",
    "t3.py": "G03_quem_liga_menos.py",
    "c1.py": "H01_trechos_e_rebrota.py",
    "m1.py": "H02_modelo1_dados.py",
    "m2.py": "H03_modelo1_treino_avaliacao.py",
    "m3.py": "H04_precisao_por_escala.py",
    "leak.py": "H05_acerto_por_escala_e_vazamento.py",
    "b1.py": "H06_lista_trechos_prioritarios.py",
    "b2.py": "H07_serie_mensal_light.py",
    "ev.py": "H08_pratica_atual_fechamentos.py",
    "ev2.py": "H09_fechamento_em_massa.py",
    "ev3.py": "H10_repeticao_com_fechados_em_massa.py",
    "janlib.py": "I01_janelas_biblioteca.py",
    "jan.py": "I02_frentes_conexas.py",
    "jan2.py": "I03_frentes_algoritmo_guloso.py",
    "n1.py": "I04_sazonalidade_e_clima_light.py",
    "n2.py": "I05_arvores_e_construcao_light.py",
    "n3.py": "I06_frentes_estoque_atual_e_vizinhos.py",
    "n4.py": "I07_vizinhos_controle.py",
    "rank1.py": "J01_prob_modelo_por_trecho_hoje.py",
    "rank2.py": "J02_sinais_por_cep.py",
    "rank3.py": "J03_nota_por_cep.py",
    "rank4.py": "J04_csv_e_dados_da_pagina.py",
    "rank_bt.py": "J05_validacao_inicial_ranking.py",
    "pri_feat.py": "J07_sinais_em_varias_datas.py",
    "pri_eval.py": "J08_avaliar_sinais.py",
    "pri_opt.py": "J09_otimizar_pesos.py",
    "pri_gbm.py": "J10_comparar_com_gbm.py",
    "pri_roll.py": "J11_dados_8_cortes.py",
    "pri_rob.py": "J12_robustez_dos_pesos.py",
    "pri_loo.py": "J13_deixar_um_periodo_de_fora.py",
    "ifnot.py": "J14_nota_como_chance.py",
    "served.py": "J15_atendido_vs_nao_atendido.py"
}

def etapa(nome_original):
    """Caminho do arquivo da etapa que corresponde a um script original."""
    return os.path.join(ETAPAS, ORIGEM[nome_original])

for _p in (TRABALHO, SAIDAS):
    os.makedirs(_p, exist_ok=True)
os.chdir(TRABALHO)

__all__ = ['os', 'RAIZ', 'ETAPAS', 'ENTRADA', 'TRABALHO', 'SAIDAS', 'SETOR', 'CLIMA_OPENMETEO',
           'CLIMA_ESTACOES_ZIP', 'ORIGEM', 'etapa']
