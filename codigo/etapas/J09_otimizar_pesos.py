"""
Ranking "Onde podar agora" · J09 — Busca dos pesos
Tipo: principal

O que faz:
    Busca local de pesos (passos de 5 pontos) que maximiza o acerto médio; treina em 2024 e
    testa em 2025.

Lê:
    código de J08_avaliar_sinais.py
Grava:
    pri_opt.pkl
Usado em:
    Escolha dos pesos 25/15/40/10/10.
Script original da análise: light/pri_opt.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np, pickle
exec(open(etapa('pri_eval.py')).read().split("rows=[]")[0])
KS=(200,500,1000)
def obj(keys,w,Ts):
    return np.mean([ev(O[T],score(C[T],dict(zip(keys,w))),KS)['obj'] for T in Ts])
def opt(keys,w0,Ts,step=5):
    w=list(w0); best=obj(keys,w,Ts); imp=True
    while imp:
        imp=False
        for i in range(len(keys)):
            for j in range(len(keys)):
                if i==j or w[j]<step: continue
                w2=w.copy(); w2[i]+=step; w2[j]-=step; v=obj(keys,w2,Ts)
                if v>best+1e-4: best,w,imp=v,w2,True
    return w,best
sets={
 'atual (5 sinais)':['risco','com','light','prev','esp'],
 '+ espaciais':['risco','com','light','prev','esp','light150','queda300','qcell'],
 'tudo':['risco','com','light','prev','esp','light150','queda300','qcell','semprev','arv','light2y'],
 'dedup':['risco_u','com_u','light_u','prev','esp'],
}
res=[]
for name,keys in sets.items():
    w0=[base.get(k,0) for k in keys]
    if sum(w0)==0: w0=[20,25,25,20,10]
    for trainTs in (['2024-07-01'],['2024-07-01','2025-01-01']):
        w,b=opt(keys,w0,trainTs)
        tests=[T for T in ['2025-01-01','2025-07-01'] if T not in trainTs]
        r={'conj':name,'treino':'+'.join(t[:7] for t in trainTs),'pesos':dict((k,v) for k,v in zip(keys,w) if v>0),'obj_treino':round(b,3)}
        for T in tests:
            e=ev(O[T],score(C[T],dict(zip(keys,w))),KS); e0=ev(O[T],score(C[T],base),KS)
            r[f'obj {T[:7]}']=round(e['obj'],3); r[f'obj atual {T[:7]}']=round(e0['obj'],3)
        res.append(r); print(r,flush=True)
pickle.dump(res,open('pri_opt.pkl','wb'))
