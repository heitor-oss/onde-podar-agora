"""
Árvores e rede elétrica: trechos e modelo 1 · H04 — Acerto por escala (trecho, 500 números, rua)
Tipo: principal

O que faz:
    Repete a regra "mais pendentes" em trechos de 100, 300 e 500 números e na rua inteira.

Lê:
    df.pkl
Grava:
    m3_res.json
Usado em:
    Página Light.
Script original da análise: light/m3.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np, json
df=pd.read_pickle('df.pkl')
df=df[df.id_logradouro.notna()&(df.numero_logradouro>0)&(df.numero_logradouro<100000)&df.subtipo.str.contains('Poda')].copy()
df['lg']=df.id_logradouro.astype('int64'); df['pend']=df.status.eq('Pendente')
T=pd.Timestamp('2025-01-01')
res={}
for unit,size in [('100 m',100),('300 m',300),('500 m',500),('rua inteira',None)]:
    key=df.lg.astype(str) if size is None else df.lg.astype(str)+'_'+(df.numero_logradouro//size).astype('int64').astype(str)
    df['u']=key
    h=df[df.ini<T]; 
    sc=h.groupby('u').agg(pa=('pend','sum'),last=('ini','max'),pod=('pend','size'))
    sc=sc[sc.pa>0]
    sc['score']=sc.pa+ (sc['last']-T).dt.days/100000
    o=sc.sort_values('score',ascending=False)
    for H in [12,18]:
        f=df[(df.ini>=T)&(df.ini<T+pd.DateOffset(months=H))&df.pend]
        yy=f.groupby('u').size()
        hit=o.index.isin(yy.index)
        r={k:float(hit[:k].mean()) for k in [100,300,500,1000]}
        # share of future pendente requests inside top k units
        cov={k:float(yy.reindex(o.index[:k]).fillna(0).sum()/yy.sum()) for k in [100,300,500,1000]}
        res[f'{unit}|{H}']=dict(prec=r,cov=cov,n_units_hist=len(sc))
        print(unit,H,'prec',{k:round(v,2) for k,v in r.items()},'cobre % pedidos',{k:round(v,2) for k,v in cov.items()})
# length estimate of street (span of numbers)
span=df.groupby('lg').numero_logradouro.agg(lambda s:s.quantile(.95)-s.quantile(.05))
print('span numeração por rua (m aprox)',span.describe(percentiles=[.5,.9]))
# share of 2025 pendente requests on trechos(100m) with pendente before 2025
df['u']=df.lg.astype(str)+'_'+(df.numero_logradouro//100).astype('int64').astype(str)
before=set(df[(df.ini<T)&df.pend].u); f=df[(df.ini>=T)&(df.ini<T+pd.DateOffset(months=12))&df.pend]
print('2025 pendentes',len(f),'em trechos com pendente anterior',f.u.isin(before).mean())
res['repeat_share_2025']=float(f.u.isin(before).mean()); res['n_pend_2025']=len(f); res['backlog_trechos']=len(before)
json.dump(res,open('m3_res.json','w'),ensure_ascii=False)
