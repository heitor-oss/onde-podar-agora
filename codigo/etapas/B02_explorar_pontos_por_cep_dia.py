"""
Picos de chamados por CEP · B02 — Exploração: quantos endereços por CEP-dia
Tipo: exploratório

O que faz:
    Conta, para cada CEP e dia, quantos chamados e quantos pontos diferentes houve, para
    separar vários chamados sobre a mesma árvore de problemas espalhados.

Lê:
    full.pkl
Grava:
    nada (só imprime resultados)
Usado em:
    Definição de pico.
Script original da análise: a2.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np
df=pd.read_pickle('full.pkl')
df=df[df.cep.notna()].copy()
df['pt']=df.latitude_usada.round(5).astype(str)+'_'+df.longitude_usada.round(5).astype(str)+'_'+df.numero_logradouro.fillna(-1).astype(str)
g=df.groupby(['cep','d']).agg(n=('id_chamado','size'),pts=('pt','nunique'),fall=('subtipo',lambda s:(s=='Retirada de árvore caída').sum()))
print(g.pts.value_counts().sort_index().tail(15))
for k in [3,4,5,6,8]: print('pts>=',k,(g.pts>=k).sum(), ' raw>=',k,(g.n>=k).sum())
print(g.sort_values('pts').tail(25))
