"""
Em quanto tempo um pedido vira emergência · D06 — Resumo para a página
Tipo: principal

O que faz:
    Junta os resultados de D01–D05 num JSON. Os números "pico" foram copiados da saída de
    D05.

Lê:
    P_lag.pkl, Q.pkl, q1_hz2.pkl
Grava:
    q1_out.json
Usado em:
    Página de picos.
Script original da análise: q1f.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np, pickle, json
from sklearn.neighbors import BallTree
P=pd.read_pickle('P_lag.pkl'); Q=pd.read_pickle('Q.pkl')
R=6371000.; START=pd.Timestamp('2022-09-01')
day=lambda s: s.values.astype('datetime64[s]').astype(np.int64)/86400
pdd=day(P.ini); pfim=day(P.fim.fillna(pd.Timestamp('2100-01-01'))); qd=day(Q.ini); s0=day(pd.Series([START]))[0]
indq=BallTree(np.radians(P[['latitude_usada','longitude_usada']].values),metric='haversine').query_radius(np.radians(Q[['latitude_usada','longitude_usada']].values),30/R)
lags=[]; stat=[]; sub=[]
for i,ix in enumerate(indq):
    if qd[i]-s0<730 or not len(ix): continue
    lag=qd[i]-pdd[ix]; m=(lag>0.5)&(lag<=30)
    if m.any():
        j=ix[m][np.argmin(lag[m])]; lags.append(lag[m].min())
        st='Ainda aberto quando a árvore caiu' if pfim[j]>qd[i] else ('Fechado como não atendido' if P.tipo_situacao.values[j]=='Não atendido' else 'Fechado (atendido/parcial) antes da queda')
        stat.append(st); sub.append(P.subtipo.values[j])
lags=np.array(lags); print(len(lags), np.percentile(lags,[25,50,75]).round(1))
print(pd.Series(stat).value_counts(normalize=True)); print(pd.Series(sub).value_counts(normalize=True).head())
hist=np.histogram(lags,bins=[0.5,1,2,3,5,7,10,14,21,30])[0]
H=pickle.load(open('q1_hz2.pkl','rb')); bins=np.array(H['bins']); w=np.diff(bins)
ab={}
for g,v in H['res'].items():
    a=np.array(v['real']); b=np.array(v['plac'])
    ab[g]=dict(ratio=(a/b)[:7].round(2).tolist(),real30=float((a[:4]*w[:4]/30).sum()),plac30=float((b[:4]*w[:4]/30).sum()),n=v['n'])
    print(g, ab[g])
out=dict(bins=bins.tolist(),groups=ab,queda=H['queda_side'],lag_q=np.percentile(lags,[25,50,75]).tolist(),lag_hist=hist.tolist(),
         status=pd.Series(stat).value_counts(normalize=True).to_dict(),sub=pd.Series(sub).value_counts(normalize=True).to_dict(),n_lag=len(lags),
         pico=dict(real={'3':0.139,'7':0.19,'30':0.489,'90':0.774},plac={'3':0.066,'7':0.117,'30':0.292,'90':0.547},lag_med=30))
json.dump(out,open('q1_out.json','w'),ensure_ascii=False)
