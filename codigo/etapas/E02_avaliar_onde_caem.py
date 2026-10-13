"""
Dado um temporal, onde caem as árvores · E02 — Quanto cada informação acerta onde caem
Tipo: principal

O que faz:
    Compara listas de quadrados (histórico, pedidos recentes, chuva local, modelos de
    Poisson) pela fração das quedas capturadas.

Lê:
    q2_rows.pkl
Grava:
    q2_summ.json
Usado em:
    Mesma pergunta.
Script original da análise: q2eval.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np, pickle, json
from sklearn.linear_model import PoissonRegressor
Z=pickle.load(open('q2_rows.pkl','rb')); rows=Z['rows']; days=Z['days']
rng=np.random.default_rng(0)
K=[0.05,0.10,0.20]
def capture(score,y,act):
    idx=np.where(act)[0]; sc=score[idx]+rng.uniform(0,1e-6,len(idx)); yy=y[idx]
    o=np.argsort(-sc); out={}
    tot=y.sum()  # include quedas in inactive cells as misses
    for k in K:
        n=int(np.ceil(k*len(idx))); out[k]=yy[o[:n]].sum()/max(tot,1)
    return out
names=['Chamados (todos) no histórico','Quedas no histórico','Quedas em eventos anteriores','Pedidos nos últimos 30 dias','Pedidos últimos 7 dias','Pedidos pendentes / não atendidos']
lf=lambda X: np.log1p(X)
res={n:[] for n in ['Acaso (célula sorteada)']+names+['Modelo: histórico combinado','Chuva local (estações)','Modelo: histórico + chuva local','Modelo: histórico (mesmos eventos)']}
tot=[]
for i,r in enumerate(rows):
    y=r['y']; act=r['act']; tot.append(y.sum())
    res['Acaso (célula sorteada)'].append({k:k*y[act].sum()/y.sum() for k in K})
    for j,n in enumerate(names): res[n].append(capture(r['X'][:,j].astype(float),y,act))
    if i>=15:
        Xtr=np.vstack([lf(rows[t]['X'][rows[t]['act']]) for t in range(i)]); ytr=np.concatenate([rows[t]['y'][rows[t]['act']] for t in range(i)])
        m=PoissonRegressor(alpha=1e-3,max_iter=500).fit(Xtr,ytr)
        res['Modelo: histórico combinado'].append(capture(m.predict(lf(r['X'])),y,act))
    else: res['Modelo: histórico combinado'].append(None)
    if r['rain'] is not None:
        res['Chuva local (estações)'].append(capture(r['rain'],y,act))
        prev=[t for t in range(i) if rows[t]['rain'] is not None]
        if len(prev)>=10:
            F=lambda rr: np.c_[lf(rr['X']),np.log1p(rr['rain'])]
            Xtr=np.vstack([F(rows[t])[rows[t]['act']] for t in prev]); ytr=np.concatenate([rows[t]['y'][rows[t]['act']] for t in prev])
            m=PoissonRegressor(alpha=1e-3,max_iter=500).fit(Xtr,ytr); res['Modelo: histórico + chuva local'].append(capture(m.predict(F(r)),y,act))
            Xtr=np.vstack([lf(rows[t]['X'])[rows[t]['act']] for t in prev])
            m2=PoissonRegressor(alpha=1e-3,max_iter=500).fit(Xtr,ytr); res['Modelo: histórico (mesmos eventos)'].append(capture(m2.predict(lf(r['X'])),y,act))
            continue
    res['Modelo: histórico + chuva local'].append(None); res['Modelo: histórico (mesmos eventos)'].append(None)
    if r['rain'] is None: res['Chuva local (estações)'].append(None)
tot=np.array(tot)
summ={}
for n,L in res.items():
    ok=[(l,t) for l,t in zip(L,tot) if l is not None]
    w=np.array([t for _,t in ok]); summ[n]={str(k):float(np.sum([l[k]*t for l,t in ok])/w.sum()) for k in K}; summ[n]['n_eventos']=len(ok); summ[n]['quedas']=int(w.sum())
    print(f"{n:42s} ev={len(ok):3d} q={int(w.sum()):5d} ", {k:round(v,3) for k,v in summ[n].items() if k in ('0.05','0.1','0.2')})
json.dump(summ,open('q2_summ.json','w'),ensure_ascii=False)
