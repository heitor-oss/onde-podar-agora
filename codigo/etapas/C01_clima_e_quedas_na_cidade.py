"""
Clima · C01 — Clima × quedas na cidade
Tipo: principal

O que faz:
    Junta o clima diário às quedas por dia e mede quanto cada variável de clima separa os
    dias de temporal (AUC).

Lê:
    clima.pkl, mats.npz
Grava:
    cityday.pkl
Usado em:
    Página de picos; base de C02.
Script original da análise: w1.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import LogisticRegression
w=pd.read_pickle('clima.pkl')   # clima diário, gerado pela etapa A03
z=np.load('mats.npz',allow_pickle=True); days=pd.DatetimeIndex(z['days'])
cf=pd.Series(z['FALL'].sum(0),days); tot=pd.Series(z['ALL'].sum(0),days)
d=w.loc[days].copy(); d['quedas']=cf.values; d['tot']=tot.values; d['storm']=(d.quedas>=40).astype(int)
print(d[['quedas','chuva_media','chuva_max','chuva_hora_max','rajada_max','chuva_3d_ant']].corr(method='spearman')['quedas'])
print(d[d.storm==1][['quedas','chuva_media','chuva_max','chuva_hora_max','rajada_max','chuva_3d_ant']].sort_values('quedas',ascending=False).to_string())
print(d[['chuva_media','chuva_max','chuva_hora_max','rajada_max']].describe(percentiles=[.5,.9,.95,.99]).round(1))
for c in ['chuva_media','chuva_max','chuva_hora_max','rajada_max','chuva_3d_ant']: print(c,'AUC storm',round(roc_auc_score(d.storm,d[c].fillna(0)),3))
d.to_pickle('cityday.pkl')
