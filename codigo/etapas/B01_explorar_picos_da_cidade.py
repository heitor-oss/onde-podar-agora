"""
Picos de chamados por CEP · B01 — Exploração: dias de pico na cidade
Tipo: exploratório

O que faz:
    Compara o total de chamados de cada dia com a mediana das 4 semanas anteriores e lista
    os maiores dias de quedas.

Lê:
    full.pkl
Grava:
    nada (só imprime resultados)
Usado em:
    Primeira exploração; não gera arquivo.
Script original da análise: a1.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np
df=pd.read_pickle('full.pkl')
df['t']=pd.to_datetime(df.data_inicio)
EMERG=['Retirada de árvore caída','Avaliação de risco de queda da árvore']
df['emerg']=df.subtipo.isin(EMERG)
city=df.groupby('d').size()
cityfall=df[df.subtipo=='Retirada de árvore caída'].groupby('d').size().reindex(city.index,fill_value=0)
base=city.rolling(28,min_periods=7).median().shift(1)
ratio=city/base
print(ratio.sort_values().tail(15))
print(cityfall.sort_values().tail(15))
print(cityfall.describe())
