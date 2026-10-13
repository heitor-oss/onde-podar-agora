"""
Prontidão em dias de temporal (modelo 3) · F02 — Modelo 3: regressão de Poisson para prontidão
Tipo: principal

O que faz:
    Regressão de Poisson por quadrado-dia com camadas (mapa fixo, pedidos recentes, cidade
    ontem, clima do dia com interações) e gradient boosting para comparação. Mede a fração
    das quedas capturada com 0,5% a 10% dos quadrados-dia em alerta.

Lê:
    clima.pkl, q7mats.npz
Grava:
    q7_pred.pkl, q7_res.json
Usado em:
    Documento de aprendizado de máquina; página de picos.
Script original da análise: q7.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np, json, pickle
from sklearn.linear_model import PoissonRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
z=np.load('q7mats.npz'); A,QM,PR,RK,BK=[z[k] for k in ['A','QM','PR','RK','BK']]
NC,D=A.shape; days=pd.date_range('2022-09-01','2026-09-20')
cum=lambda M: np.concatenate([np.zeros((NC,1),np.float32),M.cumsum(1)],1)
cA,cQ,cP,cR=cum(A),cum(QM),cum(PR),cum(RK)
w=pd.read_pickle('clima.pkl'); w=w.reindex(pd.date_range('2022-08-01','2026-09-30'))
W=w.loc[days]; Wy=w.shift(1).loc[days]
start=120  # need some history
dd=np.arange(start,D)
def seg(C,a,b): return C[:,np.clip(b,0,D)]-C[:,np.clip(a,0,D)]
F={}
F['hist_all']=cA[:,dd]                       # all chamados before d
F['hist_q']=cQ[:,dd]
F['q365']=seg(cQ,dd-365,dd)
F['p30']=seg(cP,dd-30,dd); F['p7']=seg(cP,dd-7,dd)
F['r14']=seg(cR,dd-14,dd)
F['bk']=BK[:,dd-1]
cityq=QM.sum(0); F['city_q_ontem']=np.broadcast_to(cityq[dd-1],(NC,len(dd)))
wx={'chuva':W.chuva_media.values,'chuva_h':W.chuva_hora_max.values,'rajada':W.rajada_max.values,
    'chuva_ont':Wy.chuva_media.values,'rajada_ont':Wy.rajada_max.values,'chuva7':W.chuva_7d_ant.values}
for k,v in wx.items(): F[k]=np.broadcast_to(v[dd],(NC,len(dd)))
y=QM[:,dd]
names=list(F); X=np.stack([np.asarray(F[k],np.float32).ravel() for k in names],1); Y=y.ravel()
dayidx=np.broadcast_to(dd,(NC,len(dd))).ravel(); cellidx=np.broadcast_to(np.arange(NC)[:,None],(NC,len(dd))).ravel()
split=(pd.Timestamp('2025-01-01')-days[0]).days
tr=dayidx<split; te=~tr
L=np.log1p(np.clip(X,0,None))
# weather transforms: rajada scaled (km/h) -> use (rajada-40)/10 positive part
def design(cols,inter=False):
    ix=[names.index(c) for c in cols]; M=L[:,ix]
    if inter:
        h=L[:,names.index('hist_all')][:,None]
        wcols=[c for c in cols if c in ('chuva','chuva_h','rajada','chuva_ont','rajada_ont','chuva7','city_q_ontem')]
        M=np.c_[M,h*L[:,[names.index(c) for c in wcols]]]
    return M
loc=['hist_all','hist_q','q365','p30','p7','r14','bk']
wcols=['chuva','chuva_h','rajada','chuva_ont','rajada_ont','chuva7']
S={'Mapa fixo (só histórico)':['hist_all'],
   'Histórico + pedidos recentes':loc,
   '+ cidade na véspera':loc+['city_q_ontem'],
   '+ clima do dia':loc+['city_q_ontem']+wcols}
pred={}
for n,cols in S.items():
    Xd=design(cols,inter=(n=='+ clima do dia'))
    mu=Xd[tr].mean(0); sd=Xd[tr].std(0)+1e-9
    m=PoissonRegressor(alpha=1e-4,max_iter=1000).fit((Xd[tr]-mu)/sd,Y[tr]); pred[n]=m.predict((Xd[te]-mu)/sd)
    print(n,'done')
# GBM with all
cols=loc+['city_q_ontem']+wcols; ix=[names.index(c) for c in cols]
g=HistGradientBoostingRegressor(loss='poisson',max_iter=300,learning_rate=0.05,max_leaf_nodes=31,min_samples_leaf=200,random_state=0).fit(X[tr][:,ix],Y[tr])
pred['+ clima do dia (boosting)']=g.predict(X[te][:,ix])
# oracle: city quedas today
o=np.broadcast_to(cityq[dd],(NC,len(dd))).ravel()
Xo=np.c_[design(loc),np.log1p(o)[:,None],design(['hist_all'])*np.log1p(o)[:,None]]
mu=Xo[tr].mean(0); sd=Xo[tr].std(0)+1e-9
pred['Referência: quedas da cidade no dia']=PoissonRegressor(alpha=1e-4,max_iter=1000).fit((Xo[tr]-mu)/sd,Y[tr]).predict((Xo[te]-mu)/sd)
Yt=Y[te]; dte=dayidx[te]; cte=cellidx[te]
rng=np.random.default_rng(0)
budgets=[0.005,0.01,0.02,0.05,0.10]
res={}
for n,p in pred.items():
    o=np.argsort(-(p+rng.uniform(0,1e-9,len(p)))); cs=np.cumsum(Yt[o])/Yt.sum()
    res[n]={str(b):float(cs[int(b*len(p))-1]) for b in budgets}
    # fixed per-day budget: top k cells each day (k = budget*NC)
    print(f'{n:40s}',{b:round(v,3) for b,v in res[n].items()})
# per-day fixed vs variable for best model
best='+ clima do dia'
p=pred[best]; ndays=len(np.unique(dte))
dfp=pd.DataFrame({'d':dte,'c':cte,'p':p,'y':Yt})
for b in [0.01,0.02,0.05]:
    k=int(round(b*NC))
    fixed=dfp.sort_values(['d','p'],ascending=[True,False]).groupby('d').head(k).y.sum()/Yt.sum()
    print('per-day fixed',b,k,'cells/day capture',round(fixed,3))
pickle.dump(dict(pred=pred,Yt=Yt,dte=dte,cte=cte,res=res),open('q7_pred.pkl','wb'))
json.dump(res,open('q7_res.json','w'),ensure_ascii=False)
