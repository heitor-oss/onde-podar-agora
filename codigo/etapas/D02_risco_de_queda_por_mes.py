"""
Em quanto tempo um pedido vira emergência · D02 — Quedas por mês depois do pedido × data sorteada
Tipo: exploratório

O que faz:
    Taxa de quedas próximas por mês depois do pedido, comparada com datas sorteadas
    (placebo).

Lê:
    P_lag.pkl, Q.pkl
Grava:
    q1_hz.pkl
Usado em:
    Exploração para D03.
Script original da análise: q1b.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np
from sklearn.neighbors import BallTree
P=pd.read_pickle('P_lag.pkl'); Q=pd.read_pickle('Q.pkl')
R=6371000.; rad=30
START=pd.Timestamp('2022-09-01'); END=pd.Timestamp('2026-09-20')
tq=BallTree(np.radians(Q[['latitude_usada','longitude_usada']].values),metric='haversine')
ind=tq.query_radius(np.radians(P[['latitude_usada','longitude_usada']].values), rad/R)
qd=Q.ini.values.astype('datetime64[s]').astype(np.int64)/86400
pd_=P.ini.values.astype('datetime64[s]').astype(np.int64)/86400
rng=np.random.default_rng(1)
s0=START.value/1e9/86400; e0=END.value/1e9/86400
plac=rng.uniform(s0,e0-1,len(P))
H=730; bins=np.arange(0,H+1,30)
def hz(anchor,mask):
    cnt=np.zeros(len(bins)-1); risk=np.zeros(len(bins)-1)
    fu=e0-anchor
    for i in np.where(mask)[0]:
        ix=ind[i]
        if len(ix):
            l=qd[ix]-anchor[i]; l=l[(l>0.5)&(l<=H)&(l<=fu[i])]
            if len(l): cnt+=np.histogram(l,bins)[0]
    for j in range(len(bins)-1):
        risk+= 0
    # person-time: number of P with fu >= bin end
    for j in range(len(bins)-1):
        risk[j]=(fu[mask]>=bins[j+1]).sum()
    return cnt/np.maximum(risk,1)*1000  # quedas per 1000 requests per 30d
groups={'Todos':np.ones(len(P),bool)}
for g in ['Atendido','Não atendido','Ainda aberto','Parcial']: groups[g]=(P.grupo==g).values
groups['Avaliação de risco']=(P.subtipo=='Avaliação de risco de queda da árvore').values
groups['Avaliação de risco, não atendida/aberta']=groups['Avaliação de risco']&P.grupo.isin(['Não atendido','Ainda aberto']).values
groups['Poda']=P.subtipo.str.contains('Poda').values
res={}
for g,m in groups.items():
    a=hz(pd_,m); b=hz(plac,m); res[g]=(a,b)
    print(f"{g:42s} n={m.sum():6d} real: {np.round(a[:6],2)} ... 1y:{a[:12].sum():.1f}  | placebo: {np.round(b[:6],2)} 1y:{b[:12].sum():.1f}  ratio1m {a[0]/b[0]:.2f}")
import pickle; pickle.dump(dict(res=res,bins=bins,n={g:int(m.sum()) for g,m in groups.items()}),open('q1_hz.pkl','wb'))
