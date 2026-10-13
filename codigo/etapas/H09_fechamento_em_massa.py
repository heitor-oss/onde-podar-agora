"""
Árvores e rede elétrica: trechos e modelo 1 · H09 — O fechamento em massa de outubro de 2025
Tipo: principal

O que faz:
    Descreve os 4 mil pedidos fechados em 13–14/10/2025.

Lê:
    P.pkl
Grava:
    nada (só imprime resultados)
Usado em:
    Limites.
Script original da análise: light/ev2.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np
from sklearn.neighbors import BallTree
P=pd.read_pickle('P.pkl')
P=P[P.nome_unidade_organizacional.eq('COMLURB - Companhia Municipal de Limpeza Urbana')].copy()
P['dur']=(P.fim-P.ini).dt.days; P['fd']=P.fim.dt.normalize()
S=P[P.status.isin(['Fechado com solução','Fechado com providências'])&P.fim.notna()]
purge=S.fd.isin([pd.Timestamp('2025-10-13'),pd.Timestamp('2025-10-14')])
x=S[purge]; print('fechados em 13-14/out/2025:',len(x),'espera mediana',x.dur.median(),'status',x.status.value_counts().to_dict(),'subtipo',x.subtipo.value_counts().head(3).to_dict())
print('ano de abertura',x.ini.dt.year.value_counts().sort_index().to_dict())
# all statuses closed on those days (not only served)
y=P[P.fd.isin([pd.Timestamp('2025-10-13'),pd.Timestamp('2025-10-14')])]; print('todos fechados nesses dias',len(y),y.status.value_counts().to_dict())
L=S[(S.dur>365)&~purge&S.latitude_usada.notna()]
print('fechamentos longos fora do mutirão',len(L),L.groupby(L.fd.dt.year).size().to_dict())
R=6371000;ev=[]
for d,g in L.groupby('fd'):
    X=np.radians(g[['latitude_usada','longitude_usada']].values); nb=BallTree(X,metric='haversine').query_radius(X,300/R)
    seen=np.zeros(len(g),bool)
    for i in range(len(g)):
        if seen[i]: continue
        st=[i];c=0;seen[i]=True
        while st:
            k=st.pop();c+=1
            for j in nb[k]:
                if not seen[j]:seen[j]=True;st.append(j)
        ev.append(c)
ev=np.array(ev); print('eventos',len(ev),'pedidos',ev.sum(),'média',round(ev.mean(),2),'em grupos ≥2',round(ev[ev>=2].sum()/ev.sum(),3))
print(pd.Series(ev).value_counts().sort_index().to_dict())
