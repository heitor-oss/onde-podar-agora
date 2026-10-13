"""
Em quanto tempo um pedido vira emergência · D03 — Quantas quedas tiveram pedido antes, e quanto antes
Tipo: principal

O que faz:
    Olha cada queda e procura pedidos a até 30 m no ano anterior; compara a mesma posição um
    ano antes (controle sazonal).

Lê:
    P_lag.pkl, Q.pkl
Grava:
    q1_hz2.pkl, q1_queda.pkl
Usado em:
    Mesma pergunta.
Script original da análise: q1c.py
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
# queda side
rows=[]
for i,ix in enumerate(indq):
    if qd[i]-s0<365: continue
    if len(ix)==0: rows.append((i,np.nan,None,None,None)); continue
    lag=qd[i]-pdd[ix]; m=(lag>0.5)&(lag<=365)
    if not m.any(): rows.append((i,np.nan,None,None,None)); continue
    j=ix[m][np.argmin(lag[m])]; l=lag[m].min()
    aberto = pfim[j]>qd[i]  # request not closed when tree fell
    rows.append((i,l,P.grupo.iloc[j],P.subtipo.iloc[j],aberto))
Z=pd.DataFrame(rows,columns=['i','lag','grupo','subtipo','aberto_na_queda'])
n=len(Z); has=Z.lag.notna()
print('quedas c/ 1+ ano historico',n,'com pedido previo <=365d em 30m',has.mean())
for T in [7,30,90,180,365]: print(T,(Z.lag<=T).mean())
print('lag quantis',Z.lag.quantile([.1,.25,.5,.75,.9]).round(0).to_dict())
print(Z[has].grupo.value_counts(normalize=True)); print(Z[has].subtipo.value_counts(normalize=True))
print('aberto na queda',Z[has].aberto_na_queda.mean())
print(pd.crosstab(Z[has].grupo, Z[has].aberto_na_queda,normalize='index'))
# placebo for queda side: random location? same location date shifted 1y earlier window -> fraction with request in (t-730,t-365]
rows2=[]
for i,ix in enumerate(indq):
    if qd[i]-s0<730: continue
    lag=qd[i]-pdd[ix] if len(ix) else np.array([])
    rows2.append(((lag>0.5)&(lag<=365)).any() if len(ix) else False)
    rows2[-1]=(rows2[-1], ((lag>365)&(lag<=730)).any() if len(ix) else False)
r2=np.array(rows2); print('quedas >=2y hist: pedido no ano anterior',r2[:,0].mean(),'pedido 1-2 anos antes',r2[:,1].mean())
Z.to_pickle('q1_queda.pkl')
# fine hazard daily first 90 days, real vs seasonal placebo (same location, anchor shifted -365 or +365)
indp=BallTree(np.radians(Q[['latitude_usada','longitude_usada']].values),metric='haversine').query_radius(np.radians(P[['latitude_usada','longitude_usada']].values), rad/R)
bins=np.array([0.5,3,7,14,30,60,90,180,365])
def hz(anchor,mask):
    cnt=np.zeros(len(bins)-1); fu=e0-anchor
    ok=mask&(anchor>=s0)&(anchor<=e0)
    for i in np.where(ok)[0]:
        ix=indp[i]
        if len(ix):
            l=qd[ix]-anchor[i]; l=l[(l>bins[0])&(l<=bins[-1])&(l<=fu[i])]
            if len(l): cnt+=np.histogram(l,bins)[0]
    risk=np.array([((fu>=bins[j+1])&ok).sum() for j in range(len(bins)-1)])
    w=np.diff(bins)
    return cnt/np.maximum(risk,1)/w*1000*30
shift=np.where(pdd-365>=s0,pdd-365,pdd+365)
G={'Todos os pedidos':np.ones(len(P),bool),'Avaliação de risco':(P.subtipo=='Avaliação de risco de queda da árvore').values,
   'Poda':P.subtipo.str.contains('Poda').values,'Remoção':P.subtipo.str.contains('Remoção').values,
   'Atendido':(P.grupo=='Atendido').values,'Não atendido ou aberto':P.grupo.isin(['Não atendido','Ainda aberto']).values}
res={}
for g,m in G.items():
    a=hz(pdd,m); b=hz(shift,m); res[g]=dict(real=a.tolist(),plac=b.tolist(),n=int(m.sum()))
    print(f'{g:25s}',np.round(a,1),'|',np.round(b,1))
pickle.dump(dict(res=res,bins=bins.tolist()),open('q1_hz2.pkl','wb'))
