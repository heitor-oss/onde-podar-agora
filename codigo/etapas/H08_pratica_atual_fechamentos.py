"""
Árvores e rede elétrica: trechos e modelo 1 · H08 — Como os pedidos longos são fechados hoje
Tipo: principal

O que faz:
    Pedidos atendidos depois de mais de 1 ano: quantos fecham sozinhos e quantos junto com
    vizinhos no mesmo dia.

Lê:
    P.pkl
Grava:
    nada (só imprime resultados)
Usado em:
    Página Light.
Script original da análise: light/ev.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np
from sklearn.neighbors import BallTree
P=pd.read_pickle('P.pkl'); END=pd.Timestamp('2026-09-20')
P=P[P.nome_unidade_organizacional.eq('COMLURB - Companhia Municipal de Limpeza Urbana')].copy()
P['dur']=(P.fim-P.ini).dt.days
served=P[P.status.isin(['Fechado com solução','Fechado com providências'])&P.fim.notna()]
print('podas atendidas',len(served))
print(served.dur.describe(percentiles=[.5,.75,.9,.95]))
for th in [180,365,540]:
    print('atendidas com espera >',th,'dias:',(served.dur>th).sum(), round((served.dur>th).mean(),3))
L=served[served.dur>365].copy(); L['fd']=L.fim.dt.normalize()
print('fechamentos longos por ano de fechamento',L.groupby(L.fd.dt.year).size().to_dict())
# same-day closures clustered within 300 m
L=L[L.latitude_usada.notna()]
ev=[];R=6371000
for d,g in L.groupby('fd'):
    if len(g)==1: ev.append(1); continue
    X=np.radians(g[['latitude_usada','longitude_usada']].values); t=BallTree(X,metric='haversine')
    nb=t.query_radius(X,300/R)
    seen=np.zeros(len(g),bool)
    for i in range(len(g)):
        if seen[i]: continue
        stack=[i]; comp=0; seen[i]=True
        while stack:
            k=stack.pop(); comp+=1
            for j in nb[k]:
                if not seen[j]: seen[j]=True; stack.append(j)
        ev.append(comp)
ev=np.array(ev)
print('eventos (mesmo dia, ≤300 m):',len(ev),'pedidos',ev.sum(),'média por evento',round(ev.mean(),2),'eventos com ≥2',(ev>=2).sum(),'pedidos em eventos ≥2',ev[ev>=2].sum()/ev.sum())
print(pd.Series(ev).value_counts().sort_index().head(10))
# time-of-closure patterns: weekdays, hour concentration (batch admin closure?)
L['h']=L.fim.dt.hour; print('fechamentos por dia (top)',L.groupby('fd').size().sort_values().tail(8))
