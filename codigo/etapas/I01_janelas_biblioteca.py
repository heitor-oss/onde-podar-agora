"""
Frentes de desligamento · I01 — Funções de agrupamento em frentes
Tipo: biblioteca

O que faz:
    Funções usadas por I06 e I07: estoque de pedidos por trecho numa data e agrupamento
    guloso por raio.

Lê:
    df.pkl
Grava:
    nada (só imprime resultados)
Usado em:
    I06, I07.
Script original da análise: light/janlib.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np, json
from scipy.sparse.csgraph import connected_components
from scipy.sparse import coo_matrix
from sklearn.neighbors import BallTree
df=pd.read_pickle('df.pkl')
df=df[df.id_logradouro.notna()&(df.numero_logradouro>0)&(df.numero_logradouro<100000)&df.subtipo.str.contains('Poda')].copy()
df['lg']=df.id_logradouro.astype('int64'); df['blk']=(df.numero_logradouro//100).astype('int64'); df['pend']=df.status.eq('Pendente')
df['u']=df.lg.astype(str)+'_'+df.blk.astype(str)
def build(T):
    h=df[(df.ini<T)&df.pend]
    t=h.groupby('u').agg(lg=('lg','first'),blk=('blk','first'),n=('id_chamado','size'),lat=('latitude_usada','median'),lon=('longitude_usada','median'),bairro=('bairro',lambda s:s.mode().iloc[0] if s.notna().any() else ''))
    return t
def cluster_street(t,gap=2):
    t=t.sort_values(['lg','blk']).copy(); g=[];cid=-1;prev=(None,None)
    for lg,b in zip(t.lg,t.blk):
        if lg!=prev[0] or b-prev[1]>gap: cid+=1
        g.append(cid); prev=(lg,b)
    t['jan']=g; return t
def cluster_radius(t,r=200):
    t=t.copy(); ok=t.lat.notna()
    X=np.radians(t.loc[ok,['lat','lon']].values); tr=BallTree(X,metric='haversine'); ind=tr.query_radius(X,r/6371000)
    rows=np.concatenate([np.full(len(i),k) for k,i in enumerate(ind)]); cols=np.concatenate(ind)
    n=len(X); A=coo_matrix((np.ones(len(rows)),(rows,cols)),shape=(n,n)); nc,lab=connected_components(A,directed=False)
    t['jan']=-1; t.loc[ok,'jan']=lab; m=~ok; t.loc[m,'jan']=np.arange(m.sum())+nc; return t

def greedy(t,r=150):
    t=t[t.lat.notna()].copy(); X=np.radians(t[['lat','lon']].values); tr=BallTree(X,metric='haversine')
    nb=tr.query_radius(X,r/6371000); n=t.n.values.astype(float); alive=np.ones(len(t),bool); jan=np.full(len(t),-1); score=np.array([n[i].sum() for i in nb])
    j=0
    import heapq
    while alive.any():
        sc=np.array([n[i[alive[i]]].sum() if alive[k] else -1 for k,i in enumerate(nb)]) if j%50==0 or j<5 else None
        if sc is None: sc=last
        k=int(np.argmax(sc)); members=nb[k][alive[nb[k]]]
        if len(members)==0: alive[k]=False; continue
        jan[members]=j; alive[members]=False; j+=1
        sc[members]=-1
        # update neighbours scores lazily: recompute for affected
        aff=np.unique(np.concatenate([nb[m] for m in members]))
        for a in aff:
            if alive[a]: sc[a]=n[nb[a][alive[nb[a]]]].sum()
        last=sc
    t['jan']=jan; return t
