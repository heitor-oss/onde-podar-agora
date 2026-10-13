"""
Frentes de desligamento · I07 — Vizinhos: pedidos da Light × controle
Tipo: principal

O que faz:
    Compara a fração de novos pedidos perto do estoque entre pedidos da Light e pedidos
    comuns de poda.

Lê:
    código de I01_janelas_biblioteca.py
Grava:
    nada (só imprime resultados)
Usado em:
    Página Light.
Script original da análise: light/n4.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np, json
from sklearn.neighbors import BallTree
exec(open(etapa('janlib.py')).read())
R=6371000; T=pd.Timestamp('2025-01-01'); B0=build(T); B0=B0[B0.lat.notna()]
tree=BallTree(np.radians(B0[['lat','lon']].values),metric='haversine')
f=df[(df.ini>=T)&(df.ini<T+pd.DateOffset(months=12))&df.latitude_usada.notna()]
f=f[~f.u.isin(B0.index)]
for lab,x in [('novos Light',f[f.pend]),('outros pedidos de poda (controle)',f[~f.pend])]:
    r={}
    for rr in [100,150,300]:
        c=tree.query_radius(np.radians(x[['latitude_usada','longitude_usada']].values),rr/R,count_only=True); r[rr]=float((c>0).mean())
    print(lab,len(x),r)
# trechos with any poda history (potential extra pruning) within 150 m of top-500 frentes
t=greedy(B0,150); J=t.groupby('jan').n.sum().sort_values(ascending=False)
allt=df[df.ini<T].groupby('u').agg(lat=('latitude_usada','median'),lon=('longitude_usada','median')).dropna()
for K in [500,1000]:
    mem=t[t.jan.isin(J.index[:K])]; tr2=BallTree(np.radians(mem[['lat','lon']].values),metric='haversine')
    c=tr2.query_radius(np.radians(allt[['lat','lon']].values),150/R,count_only=True)
    extra=((c>0)&~allt.index.isin(mem.index)).sum()
    print(K,'trechos da frente',len(mem),'trechos vizinhos com histórico de poda',int(extra))
