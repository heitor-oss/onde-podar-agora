"""
Frentes de desligamento · I04 — Sazonalidade e clima dos pedidos da Light
Tipo: principal

O que faz:
    Pedidos que dependem da Light por mês do ano e em dias de alerta de clima.

Lê:
    P.pkl, clima.pkl
Grava:
    n1.json
Usado em:
    Página Light.
Script original da análise: light/n1.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np, json
P=pd.read_pickle('P.pkl')  # poda requests with pend, ra, bairro
P=P[P.nome_unidade_organizacional.eq('COMLURB - Companhia Municipal de Limpeza Urbana')]
P['m']=P.ini.dt.month; P['y']=P.ini.dt.year
full=P[(P.ini>='2022-10-01')&(P.ini<'2026-09-01')]
# seasonality: Light requests per month-of-year (avg over years), and share
s=full.groupby(['y','m']).agg(n=('id_chamado','size'),l=('pend','sum')).reset_index()
s=s.groupby('m').agg(n=('n','mean'),l=('l','mean')); s['share']=s.l/s.n
print(s.round(3))
# weather relation: daily Light requests vs weather
w=pd.read_pickle('clima.pkl')
d=full.groupby(full.ini.dt.normalize()).agg(n=('id_chamado','size'),l=('pend','sum'))
d=d.join(w,how='left')
d['rajada_2d']=np.maximum(d.rajada_max,w.rajada_max.shift(1).reindex(d.index))
d['chuva_2d']=np.maximum(d.chuva_media,w.chuva_media.shift(1).reindex(d.index))
d['alerta']=(d.rajada_2d>=60)|(d.chuva_2d>=15)
print(d.groupby('alerta')[['n','l']].mean(), d.groupby('alerta').apply(lambda x:x.l.sum()/x.n.sum()))
json.dump(dict(season=dict(m=s.index.tolist(),n=s.n.round(1).tolist(),l=s.l.round(1).tolist(),share=s.share.round(4).tolist()),
 alerta={str(k):dict(n=float(v.n.mean()),l=float(v.l.mean()),share=float(v.l.sum()/v.n.sum())) for k,v in d.groupby('alerta')}),open('n1.json','w'))
