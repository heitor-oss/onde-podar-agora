"""
Ranking "Onde podar agora" · J08 — Quanto cada sinal acerta sozinho
Tipo: principal

O que faz:
    Acerto de cada sinal e da nota atual nos 200, 500 e 1.000 CEPs do topo.

Lê:
    pri_feats.pkl
Grava:
    pri_comps.pkl
Usado em:
    Melhoria da nota.
Script original da análise: light/pri_eval.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np, pickle, itertools
O=pickle.load(open('pri_feats.pkl','rb'))
L=lambda v,cap: np.clip(np.log1p(v)/np.log1p(cap),0,1)
def comps(g):
    c=pd.DataFrame(index=g.index)
    c['risco']=L(g.risco+g.queda12,12); c['risco_u']=L(g.risco_u+g.queda12,10)
    c['com']=L(g.com,8); c['com_u']=L(g.com_u,6)
    c['light']=L(g.light,12); c['light_u']=L(g.light_u,8); c['light2y']=L(g.light2y,5)
    c['prev']=np.clip((g.prob-0.07)/0.48,0,1); c['esp']=np.clip(g.esp/365,0,1)
    c['light150']=L(g.light150,25); c['queda300']=L(g.queda300,15); c['qcell']=L(g.qcell,30)
    c['semprev']=L(g.semprev,3); c['arv']=np.clip(g.arv.fillna(g.arv.median())/0.3,0,1)
    return c
Y=['y_queda','y_rq','y_light']
def ev(g,s,ks=(200,500)):
    a=g.active.values; s=np.where(a,s,-1); o=np.argsort(-s); r={}
    for k in ks:
        top=o[:k]
        for y in Y: r[f'{y}@{k}']=(g[y].values[top]>0).mean()
        r[f'quedas_cap@{k}']=g.y_queda.values[top].sum()/g.y_queda.values[a].sum()
    r['obj']=np.mean([r[f'{y}@{k}'] for y in Y for k in ks])
    return r
C={k:comps(g) for k,g in O.items()}
base={'risco':30,'com':25,'light':20,'prev':15,'esp':10}
def score(c,w): return sum(c[k].values*v for k,v in w.items())/sum(w.values())*100
rows=[]
for k in ['2024-07-01','2025-01-01','2025-07-01']:
    g=O[k]; c=C[k]; rows.append(dict(T=k,var='atual',**ev(g,score(c,base))))
    for f in c.columns: rows.append(dict(T=k,var='só '+f,**ev(g,c[f].values)))
R=pd.DataFrame(rows)
pd.set_option('display.width',250); pd.set_option('display.max_columns',20)
print(R[R['T']=='2024-07-01'].set_index('var').round(3).drop(columns='T'))
print(R[R['var']=='atual'].set_index('T').round(3))
pickle.dump(C,open('pri_comps.pkl','wb'))
