"""
Frentes de desligamento · I03 — Frentes pelo algoritmo guloso
Tipo: principal

O que faz:
    Agrupa o estoque de pedidos em frentes: pega o trecho com mais pedidos num raio, forma a
    frente, retira e repete.

Lê:
    jan.json, código de I02_frentes_conexas.py
Grava:
    backlog_now.pkl, jan.json, janelas_now.pkl
Usado em:
    Página Light; painel do piloto.
Script original da análise: light/jan2.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np, json
from sklearn.neighbors import BallTree
exec(open(etapa('jan.py')).read().split("T=pd.Timestamp('2025-01-01')")[0])
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
T=pd.Timestamp('2025-01-01')
f=df[(df.ini>=T)&(df.ini<T+pd.DateOffset(months=12))&df.pend]; yy=f.groupby('u').size(); tot=len(f)
res=json.load(open('jan.json')); res.pop('Raio de 200 m',None)
t=greedy(build(T),150); t['y']=yy.reindex(t.index).fillna(0).values
J=t.groupby('jan').agg(n=('n','sum'),y=('y','sum'),tr=('n','size')).sort_values('n',ascending=False)
cum=J.y.cumsum()/tot; cumtr=J.tr.cumsum(); out={}
for k in [100,250,500,1000]: out[k]=dict(cov=float(cum.iloc[min(k,len(J))-1]),evit=int(J.y.iloc[:k].sum()),trechos=int(cumtr.iloc[min(k,len(J))-1]))
out['n_jan']=len(J); out['cov_all']=float(J.y.sum()/tot); out['med_tr']=float(J.tr.mean()); out['k25']=int((cum<0.25).sum()+1); out['k50']=int((cum<0.5).sum()+1) if cum.iloc[-1]>=0.5 else None
res['Frente de 150 m de raio']=out; print(out)
END=pd.Timestamp('2026-09-21'); tn=greedy(build(END),150)
J=tn.groupby('jan').agg(n=('n','sum'),tr=('n','size'),lat=('lat','mean'),lon=('lon','mean'),bairro=('bairro',lambda s:s.mode().iloc[0] if (s!='').any() else '')).sort_values('n',ascending=False)
J['rank']=np.arange(1,len(J)+1); tn['jan_rank']=tn.jan.map(J['rank'])
tn.to_pickle('backlog_now.pkl'); J.to_pickle('janelas_now.pkl')
res['now']=dict(trechos=len(tn),janelas=len(J),pend=int(tn.n.sum()))
print(res['now']); print(J.head(8)); print(J.tr.describe())
json.dump(res,open('jan.json','w'),ensure_ascii=False)
