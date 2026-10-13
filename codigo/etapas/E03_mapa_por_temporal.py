"""
Dado um temporal, onde caem as árvores · E03 — Mapa de cada temporal
Tipo: principal

O que faz:
    Para cada temporal, guarda as quedas, os quadrados apontados pelo histórico e a chuva
    das estações.

Lê:
    estacoes_diario.pkl, full.pkl, q2_rows.pkl
Grava:
    q2_map.json
Usado em:
    Página de picos.
Script original da análise: q2map.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np, pickle, json
Z=pickle.load(open('q2_rows.pkl','rb')); rows=Z['rows']; days=Z['days']; cells=Z['cells']; NC=Z['NC']
df=pd.read_pickle('full.pkl'); df=df[(df.subtipo=='Retirada de árvore caída')&df.latitude_usada.notna()].copy()
df['d']=pd.to_datetime(df.data_inicio).dt.normalize()
st=pd.read_pickle('estacoes_diario.pkl')
rng=np.random.default_rng(0); ev=[]
for r in rows:
    y=r['y']
    if y.sum()<40: continue
    act=np.where(r['act'])[0]; sc=np.log1p(r['X'][act,0])+rng.uniform(0,1e-6,len(act)); n=int(np.ceil(0.1*len(act)))
    top=act[np.argsort(-sc)[:n]]
    q=df[df.d==days[r['s']]]
    pts=q[['latitude_usada','longitude_usada']].round(4).values.tolist()
    cap=y[top].sum()/y.sum()
    rain=None
    s=st[st.data==days[r['s']]]
    if len(s)>15: rain=dict(max=round(float(s.max1h.max()),1),med=round(float(s.max1h.median()),1))
    ev.append(dict(d=str(days[r['s']].date()),n=int(y.sum()),cap=round(float(cap),3),top=top.tolist(),pts=pts,rain=rain))
# history intensity per cell (all data) for background
cnt=np.zeros(NC)
for r in rows[-1:]: cnt=r['X'][:,0]
json.dump(dict(cells=cells.tolist(),ev=ev,hist=cnt.tolist()),open('q2_map.json','w'))
print(len(ev),[ (e['d'],e['n'],e['cap']) for e in ev])
