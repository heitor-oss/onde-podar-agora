"""
Preparação dos dados · A01 — Juntar as 4 partes dos chamados do 1746
Tipo: principal

O que faz:
    Lê os quatro CSVs de chamados (com CEP já atribuído), junta numa tabela só e cria a
    coluna d (dia do chamado).

Lê:
    4 partes dos chamados (dados_entrada)
Grava:
    full.pkl
Usado em:
    Base de todas as análises.
Escrito para este pacote a partir dos trechos rodados durante a análise.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import glob, re
import pandas as pd

# A ordem 1, 2, 4, 3 é a ordem em que as partes foram lidas na análise original.
# Ela não muda nenhuma contagem, mas alguns desempates ("primeiro valor do grupo",
# amostras aleatórias) dependem da ordem das linhas. Mantê-la reproduz os números publicados.
ORDEM_ORIGINAL = [1, 2, 4, 3]

arquivos = {}
for f in glob.glob(os.path.join(ENTRADA, '*chamados_completo_com_cep_parte*de4.csv')):
    arquivos[int(re.search(r'parte(\d)de4', f).group(1))] = f
faltando = [n for n in ORDEM_ORIGINAL if n not in arquivos]
if faltando:
    raise SystemExit(f'Faltam as partes {faltando} dos chamados em {ENTRADA}')

df = pd.concat([pd.read_csv(arquivos[n]) for n in ORDEM_ORIGINAL], ignore_index=True)
df['d'] = pd.to_datetime(df.data_inicio).dt.normalize()   # dia do chamado, sem a hora

# Conferências simples
assert not df.id_chamado.duplicated().any(), 'há chamados repetidos entre as partes'
print('chamados:', len(df), '| colunas:', df.shape[1])
print('período:', df.d.min().date(), 'a', df.d.max().date())
print('com CEP:', df.cep.notna().sum(), '| com coordenada usada:', df.latitude_usada.notna().sum())
print(df.subtipo.value_counts().to_string())

df.to_pickle('full.pkl')
