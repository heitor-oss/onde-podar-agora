"""
Roda as etapas em ordem. Cada etapa grava seus arquivos em trabalho/ e a saída de texto em logs/.

Uso:
    python rodar_tudo.py                 # todas as etapas
    python rodar_tudo.py J               # só as etapas do grupo J
    python rodar_tudo.py A01 A02 H03     # etapas específicas
    python rodar_tudo.py --a-partir H01  # da etapa H01 em diante
"""
import os, sys, subprocess, time

ORDEM = [
    "A01_juntar_chamados",
    "A02_base_poda_bairros_zonas",
    "A03_clima_openmeteo",
    "A04_clima_estacoes",
    "B01_explorar_picos_da_cidade",
    "B02_explorar_pontos_por_cep_dia",
    "B03_tabela_cep_dia_e_matrizes",
    "B04_eventos_e_perfil_antes_do_pico",
    "B05_comparacao_com_o_proprio_cep",
    "B06_modelo2_picos_gbm",
    "B07_modelo2_picos_logistica",
    "B08_temporais_na_cidade",
    "B09_dados_pagina_picos",
    "C01_clima_e_quedas_na_cidade",
    "C02_alerta_de_chuva_e_vento",
    "C03_modelo2_com_clima",
    "C05_modelo2_alerta_interacao",
    "D01_pedidos_e_quedas_proximas",
    "D02_risco_de_queda_por_mes",
    "D03_quedas_e_pedidos_anteriores",
    "D04_dias_calmos_e_temporais",
    "D05_chamados_antes_dos_picos",
    "D06_resumo_tempo_ate_emergencia",
    "E01_quadrados_em_dias_de_queda",
    "E02_avaliar_onde_caem",
    "E03_mapa_por_temporal",
    "E04_atualizar_durante_o_dia",
    "F01_matrizes_quadrado_dia",
    "F02_modelo3_prontidao_poisson",
    "F03_regra_de_bolso_alerta",
    "F04_exemplos_de_dias",
    "G01_setores_em_dias_de_queda",
    "G02_arvores_ajudam_a_prever",
    "G03_quem_liga_menos",
    "H01_trechos_e_rebrota",
    "H02_modelo1_dados",
    "H03_modelo1_treino_avaliacao",
    "H04_precisao_por_escala",
    "H05_acerto_por_escala_e_vazamento",
    "H06_lista_trechos_prioritarios",
    "H07_serie_mensal_light",
    "H08_pratica_atual_fechamentos",
    "H09_fechamento_em_massa",
    "H10_repeticao_com_fechados_em_massa",
    "I02_frentes_conexas",
    "I03_frentes_algoritmo_guloso",
    "I04_sazonalidade_e_clima_light",
    "I05_arvores_e_construcao_light",
    "I06_frentes_estoque_atual_e_vizinhos",
    "I07_vizinhos_controle",
    "J01_prob_modelo_por_trecho_hoje",
    "J02_sinais_por_cep",
    "J03_nota_por_cep",
    "J04_csv_e_dados_da_pagina",
    "J05_validacao_inicial_ranking",
    "J06_diagnostico_justificativas_zonas",
    "J07_sinais_em_varias_datas",
    "J08_avaliar_sinais",
    "J09_otimizar_pesos",
    "J10_comparar_com_gbm",
    "J11_dados_8_cortes",
    "J12_robustez_dos_pesos",
    "J13_deixar_um_periodo_de_fora",
    "J14_nota_como_chance",
    "J15_atendido_vs_nao_atendido",
    "J16_mapa_de_risco",
    "J17_numeros_da_pagina",
    "J18_areas_150m",
    "J19_montar_pagina"
]

def main(args):
    sel = ORDEM
    if args and args[0] == '--a-partir':
        sel = ORDEM[[e[:3] for e in ORDEM].index(args[1]):]
    elif args:
        sel = [e for e in ORDEM if any(e.startswith(a) for a in args)]
    raiz = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(os.path.join(raiz, 'logs'), exist_ok=True)
    for e in sel:
        t0 = time.time()
        print(f'→ {e} ...', end=' ', flush=True)
        with open(os.path.join(raiz, 'logs', e + '.txt'), 'w') as log:
            r = subprocess.run([sys.executable, os.path.join(raiz, 'etapas', e + '.py')], stdout=log, stderr=subprocess.STDOUT)
        print(f'{time.time() - t0:.0f} s' + ('' if r.returncode == 0 else f'  ERRO (veja logs/{e}.txt)'))
        if r.returncode != 0:
            sys.exit(r.returncode)

if __name__ == '__main__':
    main(sys.argv[1:])
