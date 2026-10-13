"""
Em quanto tempo um pedido vira emergência · D01 — Pedidos seguidos de queda a até 30 e 100 m
Tipo: principal

O que faz:
    Para cada pedido (poda, risco, remoção), procura a primeira árvore caída a até 30 m e
    100 m depois dele.

Lê:
    full.pkl
Grava:
    P_lag.pkl, Q.pkl
Usado em:
    Pergunta "em quanto tempo um pedido vira emergência".
Script original da análise: q1.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np
from sklearn.neighbors import BallTree
df=pd.read_pickle('full.pkl')
df['ini']=pd.to_datetime(df.data_inicio); df['fim']=pd.to_datetime(df.data_fim,errors='coerce')
df=df[df.latitude_usada.notna()].copy()
df['exata']=df.latitude.notna()
Q=df[df.subtipo=='Retirada de árvore caída'].copy()
P=df[df.subtipo!='Retirada de árvore caída'].copy()
def grp(r):
    if r in ('Atendido',): return 'Atendido'
    if r in ('Atendido parcialmente',): return 'Parcial'
    if r in ('Não atendido',): return 'Não atendido'
    if r=='Andamento': return 'Ainda aberto'
    return 'Outro'
P['grupo']=P.tipo_situacao.map(grp)
print(P.grupo.value_counts()); print(len(Q), Q.exata.mean(), P.exata.mean())
R=6371000.
tq=BallTree(np.radians(Q[['latitude_usada','longitude_usada']].values),metric='haversine')
END=df.ini.max()
out={}
for rad in [30,100]:
    ind=tq.query_radius(np.radians(P[['latitude_usada','longitude_usada']].values), rad/R)
    qd=Q.ini.values
    first=np.full(len(P),np.nan); 
    pdates=P.ini.values
    for i,ix in enumerate(ind):
        if len(ix)==0: continue
        dd=(qd[ix]-pdates[i])/np.timedelta64(1,'D'); dd=dd[dd>0]
        if len(dd): first[i]=dd.min()
    P[f'lag{rad}']=first
    # placebo: random date
rng=np.random.default_rng(0)
P['fu']=(END-P.ini).dt.total_seconds()/86400
P.to_pickle('P_lag.pkl'); Q.to_pickle('Q.pkl')
for rad in [30,100]:
    for g,s in P.groupby('grupo'):
        for T in [7,30,90,365]:
            elig=s[s.fu>=T]; p=(elig[f'lag{rad}']<=T).mean()
            out[(rad,g,T)]=p
    print(rad,{k:round(v*100,2) for k,v in out.items() if k[0]==rad})
