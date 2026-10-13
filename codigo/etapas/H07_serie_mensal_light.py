"""
Árvores e rede elétrica: trechos e modelo 1 · H07 — Série mensal de pedidos que dependem da Light
Tipo: principal

O que faz:
    Pedidos de poda e Pendentes por mês e por ano.

Lê:
    df.pkl
Grava:
    b2.json
Usado em:
    Sazonalidade.
Script original da análise: light/b2.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np, json
df=pd.read_pickle('df.pkl'); P=df[df.subtipo.str.contains('Poda')].copy()
P['pend']=P.status.eq('Pendente'); P['ouv']=P.nome_unidade_organizacional.eq('Ouvidoria COMLURB')
m=P[P.ini<'2026-09-01'].groupby(P.ini.dt.to_period('M')).agg(poda=('id_chamado','size'),light=('pend','sum'),ouv=('ouv','sum'),rec=('reclamacoes','sum'))
m=m[m.index>='2022-10']
m['taxa']=m.light/m.poda
print(m.to_string())
y=P.groupby(P.ini.dt.year).agg(poda=('id_chamado','size'),light=('pend','sum'),ouv=('ouv','sum'),rec=('reclamacoes','sum')); print(y)
# complaints vs Light: reclamacoes per chamado by pend
print(P.groupby('pend').reclamacoes.mean())
# share of all complaints (rec) on poda that come from Light-dependent chamados
print('share rec from pend',P[P.pend].reclamacoes.sum()/P.reclamacoes.sum())
json.dump(dict(m=dict(d=[str(i) for i in m.index],poda=m.poda.tolist(),light=m.light.astype(int).tolist(),ouv=m.ouv.astype(int).tolist(),rec=m.rec.astype(int).tolist()),
  rec_share_pend=float(P[P.pend].reclamacoes.sum()/P.reclamacoes.sum())),open('b2.json','w'))
