"""
Clima · C02 — Regra de alerta de chuva e vento
Tipo: principal

O que faz:
    Testa limites simples (rajada ≥ 60 km/h, chuva ≥ 15 mm no dia ou ≥ 8 mm em 1 hora, no
    dia ou na véspera) para marcar dias de alerta.

Lê:
    cityday.pkl, clima.pkl
Grava:
    cityday2.pkl
Usado em:
    Prontidão (F) e página de picos.
Script original da análise: w2.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
d=pd.read_pickle('cityday.pkl'); w=pd.read_pickle('clima.pkl')
for c in ['chuva_media','chuva_hora_max','rajada_max']:
    d[c+'_ontem']=w[c].shift(1).loc[d.index].values
    d[c+'_2d']=np.maximum(d[c],d[c+'_ontem'])
for c in ['chuva_media','chuva_hora_max','rajada_max']:
    print(c, 'AUC t',round(roc_auc_score(d.storm,d[c]),3),'t-1',round(roc_auc_score(d.storm,d[c+'_ontem']),3),'max(t,t-1)',round(roc_auc_score(d.storm,d[c+'_2d']),3))
# storm days: which weather class
d['vento']=d.rajada_max_2d>=60; d['chuva']=(d.chuva_media_2d>=15)|(d.chuva_hora_max_2d>=8)
S=d[d.storm==1]; print('storm days',len(S),'vento',S.vento.mean(),'chuva',S.chuva.mean(),'algum',(S.vento|S.chuva).mean())
N=d[d.storm==0]; print('non-storm days with alert',(N.vento|N.chuva).mean(), 'n alert days',(d.vento|d.chuva).sum())
print('P(storm|alert)',d[d.vento|d.chuva].storm.mean(),'P(storm|no alert)',d[~(d.vento|d.chuva)].storm.mean())
# city quedas regression features
feats=['chuva_media','chuva_hora_max','rajada_max','chuva_media_ontem','chuva_hora_max_ontem','rajada_max_ontem','chuva_3d_ant','chuva_7d_ant']
X=np.log1p(d[feats].fillna(0)); tr=d.index<'2025-01-01'
m=make_pipeline(StandardScaler(),LogisticRegression(class_weight='balanced',C=0.5,max_iter=2000)).fit(X[tr],d.storm[tr])
p=m.predict_proba(X[~tr])[:,1]; print('city storm model AUC test',roc_auc_score(d.storm[~tr],p))
print(dict(zip(feats,m[-1].coef_[0].round(2))))
# quedas correlation spearman with 2d
print(d[['quedas','chuva_media_2d','chuva_hora_max_2d','rajada_max_2d']].corr('spearman')['quedas'])
d.to_pickle('cityday2.pkl')
# precision at top days
o=pd.Series(p,d.index[~tr]); st=d.storm[~tr]
for k in [10,20,30,60]: top=o.nlargest(k).index; print('top',k,'days -> storms',st[top].sum(),'of',st.sum())
