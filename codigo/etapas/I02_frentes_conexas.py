"""
Frentes de desligamento · I02 — Frentes por componentes conexos
Tipo: exploratório

O que faz:
    Primeira versão das frentes: trechos ligados por distância.

Lê:
    df.pkl
Grava:
    backlog_now.pkl, jan.json, janelas_now.pkl
Usado em:
    Exploração.
Script original da análise: light/jan.py
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
T=pd.Timestamp('2025-01-01')
f=df[(df.ini>=T)&(df.ini<T+pd.DateOffset(months=12))&df.pend]; yy=f.groupby('u').size(); tot=len(f)  # all 2025 pend w/ trecho
res={}
t0=build(T)
for nm,fn in [('Trecho de 100 m (sem agrupar)',lambda t: t.assign(jan=np.arange(len(t)))),('Mesma rua, trechos a até 300 m',cluster_street),('Raio de 200 m',lambda t:cluster_radius(t,200))]:
    t=fn(t0); t['y']=yy.reindex(t.index).fillna(0).values
    J=t.groupby('jan').agg(n=('n','sum'),y=('y','sum'),tr=('n','size')).sort_values('n',ascending=False)
    cum=J.y.cumsum()/tot; cumtr=J.tr.cumsum()
    out={}
    for k in [100,250,500,1000]:
        out[k]=dict(cov=float(cum.iloc[min(k,len(J))-1]),evit=int(J.y.iloc[:k].sum()),trechos=int(cumtr.iloc[min(k,len(J))-1]))
    out['n_jan']=len(J); out['cov_all']=float(J.y.sum()/tot); out['med_tr']=float(J.tr.mean())
    # janelas needed for 25% and 50%
    out['k25']=int((cum<0.25).sum()+1); out['k50']=int((cum<0.5).sum()+1) if cum.iloc[-1]>=0.5 else None
    res[nm]=out; print(nm,out)
res['tot2025']=int(tot)
# current backlog grouping for panel (as of END) using radius 200m
END=pd.Timestamp('2026-09-21'); tn=cluster_radius(build(END),200)
J=tn.groupby('jan').agg(n=('n','sum'),tr=('n','size'),lat=('lat','mean'),lon=('lon','mean'),bairro=('bairro',lambda s:s.mode().iloc[0] if (s!='').any() else '')).sort_values('n',ascending=False)
J['rank']=np.arange(1,len(J)+1)
tn['jan_rank']=tn.jan.map(J['rank'])
tn.to_pickle('backlog_now.pkl'); J.to_pickle('janelas_now.pkl')
print('backlog agora',len(tn),'janelas',len(J), J.head(10))
res['now']=dict(trechos=len(tn),janelas=len(J),pend=int(tn.n.sum()))
json.dump(res,open('jan.json','w'),ensure_ascii=False)
