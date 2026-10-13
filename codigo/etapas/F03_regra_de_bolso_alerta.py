"""
Prontidão em dias de temporal (modelo 3) · F03 — Regra de bolso de prontidão
Tipo: principal

O que faz:
    Testa a regra "10 quadrados em dias normais, 200 em dias de alerta" e resume por dia.

Lê:
    cityday2.pkl, q7_pred.pkl
Grava:
    q7_days.pkl
Usado em:
    Página de picos.
Script original da análise: q7b.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np, pickle, json
P=pickle.load(open('q7_pred.pkl','rb')); p=P['pred']['+ clima do dia']; pf=P['pred']['Histórico + pedidos recentes']
Yt,dte,cte=P['Yt'],P['dte'],P['cte']
days=pd.date_range('2022-09-01','2026-09-20'); NC=976
d2=pd.read_pickle('cityday2.pkl')
alert=((d2.rajada_max_2d>=60)|(d2.chuva_media_2d>=15)|(d2.chuva_hora_max_2d>=8))
cq=d2.quedas
df=pd.DataFrame({'d':dte,'c':cte,'p':p,'pf':pf,'y':Yt})
thr=np.quantile(p,1-0.05); df['al']=df.p>=thr
g=df.groupby('d').agg(n_al=('al','sum'),y=('y','sum'),cap=('y',lambda s: 0))
g['cap']=df[df.al].groupby('d').y.sum().reindex(g.index,fill_value=0)
g['date']=days[g.index]; g['alerta']=alert.reindex(g.date).values; g['ontem20']=cq.shift(1).reindex(g.date).values>=20
g['storm']=cq.reindex(g.date).values>=40
print(g.groupby('alerta').agg(dias=('y','size'),cel_med=('n_al','mean'),cel_mediana=('n_al','median'),quedas=('y','sum'),capt=('cap','sum')))
print(g.groupby('storm').agg(dias=('y','size'),cel_med=('n_al','mean'),quedas=('y','sum'),capt=('cap','sum')))
print(g.n_al.describe(percentiles=[.25,.5,.75,.9]))
# simple rule grid
fixedrank=df.groupby('c').pf.mean().rank(ascending=False)  # not used
best=None
for lo in [5,10,20,30]:
  for hi in [80,120,160,200,250]:
    lvl=(g.alerta|g.ontem20)
    k=np.where(lvl.reindex(df.d).values if False else lvl.values,hi,lo)
    kd=dict(zip(g.index,k))
    sel=df.assign(r=df.groupby('d').pf.rank(ascending=False,method='first'))
    sel=sel[sel.r<=sel.d.map(kd)]
    cap=sel.y.sum()/df.y.sum(); budget=len(sel)/len(df)
    print(lo,hi,round(budget,3),round(cap,3))
g.to_pickle('q7_days.pkl')
