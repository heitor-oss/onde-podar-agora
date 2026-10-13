"""
Ranking "Onde podar agora" · J03 — Ranking: nota por CEP
Tipo: principal

O que faz:
    Transforma cada sinal em 0–1 (escala log) e soma com os pesos 25/15/40/10/10.

Lê:
    cepg.pkl, df.pkl
Grava:
    cep_rank.pkl
Usado em:
    Página "Onde podar agora".
Script original da análise: light/rank3.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np, json
g=pd.read_pickle('cepg.pkl')
df=pd.read_pickle('df.pkl'); df=df[df.cep.notna()].copy(); df['cep']=df.cep.astype('int64')
md=lambda s: s.mode().iloc[0] if s.notna().any() else ''
meta=df.groupby('cep').agg(rua=('cep_logradouro_ref',md),bairro=('bairro',md),ra=('ra',md),lat=('latitude_usada','median'),lon=('longitude_usada','median'),dist=('dist_km_ao_cep','median'))
g=g.join(meta)
L=lambda v,cap: np.clip(np.log1p(v)/np.log1p(cap),0,1)
g['c_risco']=L(g.risco12+g.queda12,12); g['c_com']=L(g.comlurb,8); g['c_light']=L(g.light,12)
g['c_prev']=np.clip((g.prob-0.07)/(0.55-0.07),0,1); g['c_esp']=np.clip(g.espera_com/365,0,1)
W=dict(c_risco=25,c_com=15,c_light=40,c_prev=10,c_esp=10)
g['score']=sum(g[k]*w for k,w in W.items())
g=g[(g.comlurb+g.light+g.risco12)>0].sort_values('score',ascending=False)
pd.set_option('display.width',250)
print(g.head(40)[['rua','bairro','comlurb','light','risco12','queda12','espera_com','prob','score','dist']].round(2).to_string())
print(g.score.describe())
print((g.score>=50).sum(),(g.score>=40).sum())
g.to_pickle('cep_rank.pkl')
