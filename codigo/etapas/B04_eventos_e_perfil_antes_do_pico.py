"""
Picos de chamados por CEP · B04 — Picos por CEP e o que acontece antes deles
Tipo: principal

O que faz:
    Define pico emergencial (3+ chamados de queda ou risco em 2+ endereços no mesmo CEP e
    dia) e picos de volume (5+ chamados, "lote" no mesmo endereço ou "mutirão" na rua).
    Compara os chamados nos dias anteriores ao pico com CEPs sorteados.

Lê:
    cepday.pkl, mats.npz
Grava:
    ev.pkl, prof.json, vol.pkl
Usado em:
    Página "Picos de chamados por CEP".
Script original da análise: a4.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np, json
z=np.load('mats.npz',allow_pickle=True); ALL=z['ALL'].astype(np.int32); FALL=z['FALL'].astype(np.int32); RISK=z['RISK'].astype(np.int32)
ceps=z['ceps']; days=pd.DatetimeIndex(z['days']); C,D=ALL.shape
EM=FALL+RISK; PODA=ALL-EM
g=pd.read_pickle('cepday.pkl')
g['ci']=np.searchsorted(ceps,g.cep.values); g['di']=(g.d-days[0]).dt.days
g['em_n']=EM[g.ci,g.di]
ev=g[(g.em_n>=3)&(g.pts>=2)].copy(); ev['tipo']='Emergencial'
vol=g[(g.n>=5)&~g.index.isin(ev.index)].copy(); vol['tipo']=np.where(vol.pts<=2,'Lote','Mutirão')
print(len(ev),vol.tipo.value_counts().to_dict())
cityfall=FALL.sum(0); stormday=cityfall>=40
ev['storm']=stormday[ev.di]; print('emerg events on storm days',ev.storm.mean(), 'in +-1 day', np.mean([stormday[max(0,d-1):d+2].any() for d in ev.di]))
cum=lambda M: np.concatenate([np.zeros((M.shape[0],1),np.int32),M.cumsum(1)],1)
CA,CE,CP,CF,CR=cum(ALL),cum(EM),cum(PODA),cum(FALL),cum(RISK)
def win(Cm,ci,di,w): lo=np.maximum(di-w,0); return Cm[ci,di]-Cm[ci,lo]
# cep5 neighbours
c5=ceps//1000; u5,inv=np.unique(c5,return_inverse=True)
A5=np.zeros((len(u5),D),np.int32); np.add.at(A5,inv,ALL); E5=np.zeros_like(A5); np.add.at(E5,inv,EM)
CA5,CE5=cum(A5),cum(E5)
rng=np.random.default_rng(0)
active=np.where(ALL.sum(1)>0)[0]
def prof(E,name,K=30):
    ci,di=E.ci.values,E.di.values
    m=di>=365; ci,di=ci[m],di[m]
    cc=rng.choice(active,(len(ci),K)); dd=np.repeat(di[:,None],K,1)
    out={}
    for w in [7,30,90,365]:
        out[w]=dict(ev_mean=win(CA,ci,di,w).mean(), ctl_mean=win(CA,cc.ravel(),dd.ravel(),w).mean(),
                    ev_any=(win(CA,ci,di,w)>0).mean(), ctl_any=(win(CA,cc.ravel(),dd.ravel(),w)>0).mean(),
                    ev_em=win(CE,ci,di,w).mean(), ctl_em=win(CE,cc.ravel(),dd.ravel(),w).mean(),
                    ev_n5=win(CA5,inv[ci],di,w).mean(), ctl_n5=win(CA5,inv[cc.ravel()],dd.ravel(),w).mean())
    # self control: same cep one year before window
    sc=win(CA,ci,di-365,90).mean() if True else None
    print(name,len(ci)); 
    for w,v in out.items(): print(' ',w,{k:round(float(x),3) for k,x in v.items()})
    # event-study curve weekly
    ks=np.arange(-91,63)
    cur=[ALL[ci,np.clip(di+k,0,D-1)].mean() for k in ks]
    ctl=[ALL[cc.ravel(),np.clip(dd.ravel()+k,0,D-1)].mean() for k in ks]
    return out,ks.tolist(),cur,ctl
res={}
for name,E in [('Emergencial',ev),('Mutirão',vol[vol.tipo=='Mutirão']),('Lote',vol[vol.tipo=='Lote'])]:
    out,ks,cur,ctl=prof(E,name); res[name]=dict(win={str(k):{a:float(b) for a,b in v.items()} for k,v in out.items()},ks=ks,cur=[float(x) for x in cur],ctl=[float(x) for x in ctl],n=int(len(E)))
json.dump(res,open('prof.json','w'))
ev.to_pickle('ev.pkl'); vol.to_pickle('vol.pkl')
