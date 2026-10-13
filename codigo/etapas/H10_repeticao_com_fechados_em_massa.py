"""
Árvores e rede elétrica: trechos e modelo 1 · H10 — Repetição incluindo os fechados em massa
Tipo: principal

O que faz:
    Refaz a taxa de repetição tratando os fechados em massa como Pendentes.

Lê:
    df.pkl
Grava:
    nada (só imprime resultados)
Usado em:
    Limites.
Script original da análise: light/ev3.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np
df=pd.read_pickle('df.pkl')
df=df[df.id_logradouro.notna()&(df.numero_logradouro>0)&(df.numero_logradouro<100000)&df.subtipo.str.contains('Poda')].copy()
df['fd']=pd.to_datetime(df.data_fim,errors='coerce').dt.normalize()
purge=df.fd.isin([pd.Timestamp('2025-10-13'),pd.Timestamp('2025-10-14')])&df.status.eq('Fechado com providências')
df['u']=df.id_logradouro.astype('int64').astype(str)+'_'+(df.numero_logradouro//100).astype('int64').astype(str)
T=pd.Timestamp('2025-01-01')
for nm,lab in [('só Pendente',df.status.eq('Pendente')),('Pendente + fechados no mutirão',df.status.eq('Pendente')|purge)]:
    before=set(df[(df.ini<T)&lab].u); f=df[(df.ini>=T)&(df.ini<T+pd.DateOffset(months=12))&lab]
    print(nm,'estoque trechos',len(before),'novos 2025',len(f),'em trechos com estoque',round(f.u.isin(before).mean(),3))
