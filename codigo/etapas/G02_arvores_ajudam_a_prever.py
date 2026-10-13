"""
Cobertura de árvores · G02 — A cobertura de árvores ajuda a prever onde caem?
Tipo: principal

O que faz:
    Compara listas de setores: só árvore, só histórico, histórico + árvore.

Lê:
    t1_rows.pkl
Grava:
    t2_res.json
Usado em:
    Mesma pergunta.
Script original da análise: t2.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np, json, pickle
from sklearn.linear_model import PoissonRegressor
Z=pickle.load(open('t1_rows.pkl','rb')); rows=Z['rows']; st=Z['static']; S=Z['S']; area=S.area_km2.values
lf=np.log1p
def feats(r,kind):
    H=lf(r['X'])
    if kind=='H': return H
    if kind=='T': return st
    if kind=='HT': return np.c_[H,st,H[:,[0]]*st[:,[0]]]
rng=np.random.default_rng(0)
def capture(score,y,k,by='n'):
    if by=='a': score=score/np.maximum(area,1e-4)
    o=np.argsort(-(score+rng.uniform(0,1e-9,len(score))))
    if by=='n': n=int(np.ceil(k*len(score))); return y[o[:n]].sum()/y.sum()
    ca=np.cumsum(area[o]); n=np.searchsorted(ca,k*area.sum()); return y[o[:n]].sum()/y.sum()
K=[0.01,0.05,0.10]
res={m:{f'{b}_{k}':[] for b in ['n','a'] for k in K} for m in ['Acaso','Só árvore e ocupação','Só histórico de chamados','Histórico + árvore']}
W=[]; cold=dict(q=0,tot=0)
for i,r in enumerate(rows):
    if i<15: continue
    y=r['y']; W.append(y.sum())
    cold['q']+=y[r['X'][:,0]==0].sum(); cold['tot']+=y.sum()
    preds={'Acaso':rng.uniform(size=len(y))}
    for nm,kind in [('Só árvore e ocupação','T'),('Só histórico de chamados','H'),('Histórico + árvore','HT')]:
        Xtr=np.vstack([feats(rows[t],kind) for t in range(i)]); ytr=np.concatenate([rows[t]['y'] for t in range(i)])
        mu=Xtr.mean(0); sd=Xtr.std(0)+1e-9
        m=PoissonRegressor(alpha=1e-4,max_iter=600).fit((Xtr-mu)/sd,ytr); preds[nm]=m.predict((feats(r,kind)-mu)/sd)
    for nm,p in preds.items():
        for b in ['n','a']:
            for k in K: res[nm][f'{b}_{k}'].append(capture(p,y,k,b))
W=np.array(W,float); out={nm:{k:float(np.dot(np.array(v,float),W)/W.sum()) for k,v in d.items()} for nm,d in res.items()}
for nm,d in out.items(): print(f'{nm:28s}',{k:round(v,3) for k,v in d.items()})
print('quedas em setores sem chamado anterior',cold['q']/cold['tot'], 'eventos',len(W),'quedas',W.sum())
json.dump(dict(out=out,cold=float(cold['q']/cold['tot']),n_ev=len(W),n_q=int(W.sum())),open('t2_res.json','w'),ensure_ascii=False)
