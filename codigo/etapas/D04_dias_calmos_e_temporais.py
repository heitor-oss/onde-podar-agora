"""
Em quanto tempo um pedido vira emergência · D04 — Separando pedidos feitos perto de temporais
Tipo: principal

O que faz:
    Repete a comparação separando pedidos de dias calmos e de perto de temporais.

Lê:
    P_lag.pkl, Q.pkl, mats.npz, q1_hz2.pkl
Grava:
    q1_hz2.pkl
Usado em:
    Mesma pergunta.
Script original da análise: q1d.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np, pickle
from sklearn.neighbors import BallTree
P=pd.read_pickle('P_lag.pkl'); Q=pd.read_pickle('Q.pkl')
R=6371000.; rad=30
START=pd.Timestamp('2022-09-01'); END=pd.Timestamp('2026-09-20')
day=lambda s: s.values.astype('datetime64[s]').astype(np.int64)/86400
pdd=day(P.ini); pfim=day(P.fim.fillna(pd.Timestamp('2100-01-01'))); qd=day(Q.ini)
s0=day(pd.Series([START]))[0]; e0=day(pd.Series([END]))[0]
tp=BallTree(np.radians(P[['latitude_usada','longitude_usada']].values),metric='haversine')
indq=tp.query_radius(np.radians(Q[['latitude_usada','longitude_usada']].values), rad/R)
W=[(0.5,3),(0.5,7),(0.5,30),(0.5,90),(0.5,365)]
real={w:0 for w in W}; plac={w:0 for w in W}; n=0; unresolved=0; anyreq30=0
for i,ix in enumerate(indq):
    if qd[i]-s0<730: continue
    n+=1
    if not len(ix): continue
    lag=qd[i]-pdd[ix]
    for a,b in W:
        real[(a,b)]+=((lag>a)&(lag<=b)).any(); plac[(a,b)]+=((lag>a+365)&(lag<=b+365)).any()
    m=(lag>0.5)&(lag<=30)
    if m.any():
        anyreq30+=1
        unresolved+= (pfim[ix[m]]>qd[i]).any() | P.grupo.values[ix[m]].tolist().count('Não atendido')>0
print('n',n)
for w in W: print(w,'real',round(real[w]/n,3),'placebo(1 ano antes)',round(plac[w]/n,3),'ratio',round(real[w]/max(plac[w],1),2))
print('dos com pedido em 30d: pedido ainda aberto ou nao atendido',unresolved/anyreq30)
# storm split of request hazard
z=np.load('mats.npz',allow_pickle=True); days=pd.DatetimeIndex(z['days']); cf=z['FALL'].sum(0)
storm=set(days[cf>=40].date)
near=np.array([any((d+pd.Timedelta(days=k)).date() in storm for k in range(-3,8)) for d in P.ini.dt.normalize()])
print('requests near storm',near.mean())
indp=BallTree(np.radians(Q[['latitude_usada','longitude_usada']].values),metric='haversine').query_radius(np.radians(P[['latitude_usada','longitude_usada']].values), rad/R)
bins=np.array([0.5,3,7,14,30,60,90,180,365])
def hz(anchor,mask):
    cnt=np.zeros(len(bins)-1); fu=e0-anchor; ok=mask&(anchor>=s0)&(anchor<=e0)
    for i in np.where(ok)[0]:
        ix=indp[i]
        if len(ix):
            l=qd[ix]-anchor[i]; l=l[(l>bins[0])&(l<=bins[-1])&(l<=fu[i])]
            if len(l): cnt+=np.histogram(l,bins)[0]
    risk=np.array([((fu>=bins[j+1])&ok).sum() for j in range(len(bins)-1)])
    return cnt/np.maximum(risk,1)/np.diff(bins)*1000*30
shift=np.where(pdd-365>=s0,pdd-365,pdd+365)
res=pickle.load(open('q1_hz2.pkl','rb'))
for g,m in {'Pedidos em dias calmos':~near,'Pedidos perto de temporal':near,
            'Avaliação de risco, dia calmo':(P.subtipo=='Avaliação de risco de queda da árvore').values&~near}.items():
    a=hz(pdd,m); b=hz(shift,m); res['res'][g]=dict(real=a.tolist(),plac=b.tolist(),n=int(m.sum()))
    print(f'{g:30s}',np.round(a,1),'|',np.round(b,1))
res['queda_side']=dict(n=n,real={f'{b}':real[(a,b)]/n for a,b in W},plac={f'{b}':plac[(a,b)]/n for a,b in W},unres=unresolved/anyreq30)
pickle.dump(res,open('q1_hz2.pkl','wb'))
