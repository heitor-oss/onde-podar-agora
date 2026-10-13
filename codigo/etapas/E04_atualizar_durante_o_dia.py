"""
Dado um temporal, onde caem as árvores · E04 — Atualizar a lista com as primeiras quedas do dia
Tipo: principal

O que faz:
    Mede quanto melhora a lista quando se usam as primeiras quedas registradas no dia e os
    quadrados vizinhos.

Lê:
    full.pkl, q2_rows.pkl
Grava:
    q2_now.json
Usado em:
    Mesma pergunta.
Script original da análise: q2now.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np, pickle, json
Z=pickle.load(open('q2_rows.pkl','rb')); rows=Z['rows']; days=Z['days']; cells=Z['cells']; NC=Z['NC']
df=pd.read_pickle('full.pkl'); df=df[(df.subtipo=='Retirada de árvore caída')&df.latitude_usada.notna()].copy()
df=df[(df.latitude_usada.between(-23.1,-22.73))&(df.longitude_usada.between(-43.8,-43.09))]
df['t']=pd.to_datetime(df.data_inicio); df['d']=df.t.dt.normalize()
df['cell']=((df.longitude_usada+43.8)*102.5).astype(int)*100+((df.latitude_usada+23.1)*110.6).astype(int)
cidx={c:i for i,c in enumerate(cells)}; df['ci']=df.cell.map(cidx)
gx=cells//100; gy=cells%100; pos={c:i for i,c in enumerate(cells)}
nb=[[pos[(gx[i]+a)*100+gy[i]+b] for a in (-1,0,1) for b in (-1,0,1) if (gx[i]+a)*100+gy[i]+b in pos] for i in range(NC)]
rng=np.random.default_rng(0)
def cap(score,y,act,k=0.10):
    idx=np.where(act)[0]; sc=score[idx]+rng.uniform(0,1e-6,len(idx)); o=np.argsort(-sc); n=int(np.ceil(k*len(idx)))
    return y[idx][o[:n]].sum()/max(y.sum(),1)
R={'Histórico (antes do dia)':[],'Primeiras quedas do dia (vizinhança 3×3 km)':[],'Histórico + primeiras quedas':[]}; W=[]
for r in rows:
    day=days[r['s']]; q=df[df.d==day].sort_values('t')
    n=len(q); k=max(3,int(0.3*n)); early=q.iloc[:k]; late=q.iloc[k:]
    e=np.bincount(early.ci,minlength=NC); y=np.bincount(late.ci,minlength=NC)
    es=np.array([e[nb[i]].sum() for i in range(NC)],float)
    h=np.log1p(r['X'][:,0]); act=r['act']|(es>0)
    hz=(h-h[act].mean())/h[act].std(); ez=np.log1p(es)
    R['Histórico (antes do dia)'].append(cap(h,y,act)); R['Primeiras quedas do dia (vizinhança 3×3 km)'].append(cap(es+1e-3*h,y,act))
    R['Histórico + primeiras quedas'].append(cap(hz+1.5*ez,y,act)); W.append(y.sum())
W=np.array(W); out={k:float(np.dot(v,W)/W.sum()) for k,v in R.items()}; print(out, 'early share 30%')
json.dump(out,open('q2_now.json','w'),ensure_ascii=False)
