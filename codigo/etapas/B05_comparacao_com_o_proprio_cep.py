"""
Picos de chamados por CEP · B05 — Antes do pico × o próprio CEP em outras épocas
Tipo: principal

O que faz:
    Compara os 30 dias antes de cada pico com janelas sorteadas do mesmo CEP longe do pico.

Lê:
    ev.pkl, mats.npz, vol.pkl
Grava:
    selfctl.json
Usado em:
    Página "Picos de chamados por CEP".
Script original da análise: a5.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np, json
z=np.load('mats.npz',allow_pickle=True); ALL=z['ALL'].astype(np.int32); FALL=z['FALL'].astype(np.int32); RISK=z['RISK'].astype(np.int32)
days=pd.DatetimeIndex(z['days']); C,D=ALL.shape; EM=FALL+RISK
cum=lambda M: np.concatenate([np.zeros((M.shape[0],1),np.int32),M.cumsum(1)],1)
CA,CE=cum(ALL),cum(EM)
def seg(Cm,ci,a,b): # sum over days [a,b)
    a=np.clip(a,0,D); b=np.clip(b,0,D); return Cm[ci,b]-Cm[ci,a]
ev=pd.read_pickle('ev.pkl'); vol=pd.read_pickle('vol.pkl')
rng=np.random.default_rng(1)
out={}
for name,E in [('Emergencial',ev),('Mutirão',vol[vol.tipo=='Mutirão']),('Lote',vol[vol.tipo=='Lote'])]:
    E=E[E.di>=120]
    rows=[]
    for ci,di in zip(E.ci,E.di):
        pre=seg(CA,np.array([ci]),di-30,di-2)[0]; pre_em=seg(CE,np.array([ci]),di-30,di-2)[0]
        # self baseline: random 28-day windows of same cep, away from +-60 of this event
        cand=np.arange(30,D); cand=cand[np.abs(cand-di)>60]
        s=rng.choice(cand,200)
        base=seg(CA,np.full(200,ci),s-30,s-2); base_em=seg(CE,np.full(200,ci),s-30,s-2)
        rows.append((pre,base.mean(),pre_em,base_em.mean(),(base>=pre).mean()))
    r=np.array(rows,float)
    out[name]=dict(n=len(r),pre=r[:,0].mean(),selfbase=r[:,1].mean(),pre_em=r[:,2].mean(),selfbase_em=r[:,3].mean(),
                   frac_pre_zero=(r[:,0]==0).mean(), median_pctl=float(np.median(1-r[:,4])), frac_above_p90=float(np.mean(r[:,4]<=0.10)))
    print(name,{k:round(float(v),3) for k,v in out[name].items()})
json.dump(out,open('selfctl.json','w'))
