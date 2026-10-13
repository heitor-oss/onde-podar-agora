"""
Árvores e rede elétrica: trechos e modelo 1 · H05 — Acerto das listas por escala, vazamento, sorteio e estoque
Tipo: principal

O que faz:
    Refaz as listas "mais pendentes" (trecho, 500 números, rua; 12 e 18 meses) contando como
    pendente só pedidos com 60 ou 180 dias na data de corte, para medir o efeito de usar o
    status de hoje. Calcula também o acerto de uma lista sorteada e quanto dos novos pedidos
    de 2025 caiu nos trechos que já esperavam.

Lê:
    P.pkl, df.pkl
Grava:
    b3.json, base.json, leak.json
Usado em:
    Página Light; limites.
Script original da análise: light/leak.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np, json
df=pd.read_pickle('df.pkl')
df=df[df.id_logradouro.notna()&(df.numero_logradouro>0)&(df.numero_logradouro<100000)&df.subtipo.str.contains('Poda')].copy()
df['lg']=df.id_logradouro.astype('int64'); df['pend']=df.status.eq('Pendente')
T=pd.Timestamp('2025-01-01'); res={}
for unit,size in [('100 m',100),('500 m',500),('rua inteira',None)]:
    df['u']=df.lg.astype(str) if size is None else df.lg.astype(str)+'_'+(df.numero_logradouro//size).astype('int64').astype(str)
    f=df[(df.ini>=T)&(df.ini<T+pd.DateOffset(months=12))&df.pend]; yy=set(f.u)
    for lag in [0,60,180]:
        h=df[(df.ini<T-pd.Timedelta(days=lag))&df.pend]
        sc=h.groupby('u').agg(pa=('id_chamado','size'),last=('ini','max')); sc['s']=sc.pa+(sc['last']-T).dt.days/1e5
        o=sc.sort_values('s',ascending=False).index
        r={k:float(np.mean([u in yy for u in o[:k]])) for k in [100,300,500,1000]}
        res[f'{unit}|{lag}']=r; print(unit,'corte -',lag,'dias',{k:round(v,3) for k,v in r.items()})
# how long until status becomes final? share of requests still 'Em Andamento'/'Aberto' by age
P=pd.read_pickle('P.pkl'); END=pd.Timestamp('2026-09-20'); P['age']=(END-P.ini).dt.days
b=pd.cut(P.age,[0,30,60,90,180,365,2000]); print(P.groupby(b,observed=True).apply(lambda s: pd.Series({'pend':s.pend.mean(),'andamento':s.status.isin(['Em Andamento','Aberto']).mean()})).round(3))
# --- Mesmas listas com prazo de 18 meses (escalas de 500 números e rua inteira)
for unit,size in [('500 m',500),('rua inteira',None)]:
    df['u']=df.lg.astype(str) if size is None else df.lg.astype(str)+'_'+(df.numero_logradouro//size).astype('int64').astype(str)
    f=df[(df.ini>=T)&(df.ini<T+pd.DateOffset(months=18))&df.pend]; yy=set(f.u)
    for lag in [0,180]:
        h=df[(df.ini<T-pd.Timedelta(days=lag))&df.pend]
        sc=h.groupby('u').agg(pa=('id_chamado','size'),last=('ini','max')); sc['s']=sc.pa+(sc['last']-T).dt.days/1e5
        o=sc.sort_values('s',ascending=False).index
        res[f'{unit}|{lag}|18']={k:float(np.mean([u in yy for u in o[:k]])) for k in [100,300,500,1000]}
        print(unit,'18 meses, corte -',lag,'dias',{k:round(v,3) for k,v in res[f'{unit}|{lag}|18'].items()})
# --- Lista sorteada (base.json): acerto esperado ao escolher ao acaso entre os lugares com algum pedido de poda antes da data
base={}
for unit,size,months in [('rua inteira',None,18),('rua inteira',None,12),('500 m',500,18),('100 m',100,12)]:
    df['u']=df.lg.astype(str) if size is None else df.lg.astype(str)+'_'+(df.numero_logradouro//size).astype('int64').astype(str)
    f=df[(df.ini>=T)&(df.ini<T+pd.DateOffset(months=months))&df.pend]; yy=set(f.u)
    base[f'{unit}|{months}']=float(np.mean([u in yy for u in set(df[df.ini<T].u)]))
print('lista sorteada',{k:round(v,4) for k,v in base.items()})
json.dump(base,open('base.json','w'))
# --- Cobertura do estoque (b3.json): fração dos novos pedidos da Light de 2025 que caíram nos k trechos com mais pendentes em 01/01/2025
df['u']=df.lg.astype(str)+'_'+(df.numero_logradouro//100).astype('int64').astype(str)
h=df[(df.ini<T)&df.pend]; f=df[(df.ini>=T)&(df.ini<T+pd.DateOffset(months=12))&df.pend]
sc=h.groupby('u').agg(pa=('id_chamado','size'),last=('ini','max')); sc['s']=sc.pa+(sc['last']-T).dt.days/1e5
o=sc.sort_values('s',ascending=False).index
curva={str(k):float(f.u.isin(set(o[:k])).mean()) for k in [100,300,500,1000,2000,3000,len(o)]}
print('cobertura do estoque',{k:round(v,3) for k,v in curva.items()})
json.dump(dict(curve=curva,backlog=len(o),n_next=len(f)),open('b3.json','w'))
json.dump(res,open('leak.json','w'))
