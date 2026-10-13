"""
Frentes de desligamento · I06 — Frentes do estoque atual e poda dos vizinhos
Tipo: principal

O que faz:
    Número de desligamentos por raio (50 a 300 m) e quanto da demanda de 2025 as frentes
    cobrem incluindo vizinhos a até 150 m.

Lê:
    código de I01_janelas_biblioteca.py
Grava:
    n3.json
Usado em:
    Página Light; documento.
Script original da análise: light/n3.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np, json
from sklearn.neighbors import BallTree
exec(open(etapa('janlib.py')).read())
R=6371000
out={}
# 1) shutdown count by strategy, current backlog
END=pd.Timestamp('2026-09-21'); B=build(END)
out['pedidos']=int(B.n.sum()); out['trechos']=len(B)
rad={}
for r in [50,100,150,300]:
    t=greedy(B,r); J=t.groupby('jan').agg(n=('n','sum'),tr=('n','size')).sort_values('n',ascending=False)
    c=J.n.cumsum()/J.n.sum()
    rad[r]=dict(janelas=len(J),ped_por_jan=float(J.n.mean()),tr_por_jan=float(J.tr.mean()),k50=int((c<0.5).sum()+1),k80=int((c<0.8).sum()+1))
    print(r,rad[r])
out['raios']=rad
# 2) preventive: at 2025-01-01, new Light requests in 2025 in trechos without backlog: how many lie within r of a backlog trecho (inside a shutdown area)?
T=pd.Timestamp('2025-01-01'); B0=build(T); B0=B0[B0.lat.notna()]
f=df[(df.ini>=T)&(df.ini<T+pd.DateOffset(months=12))&df.pend&df.latitude_usada.notna()]
new=f[~f.u.isin(B0.index)]
print('2025 pend',len(f),'novos trechos',len(new))
tree=BallTree(np.radians(B0[['lat','lon']].values),metric='haversine')
prev={}
for r in [50,100,150,300]:
    cnt=tree.query_radius(np.radians(new[['latitude_usada','longitude_usada']].values),r/R,count_only=True)
    prev[r]=float((cnt>0).mean())
    print('novos dentro de',r,'m de trecho com estoque:',round(prev[r],3))
out['prev_new_within']=prev; out['n2025']=len(f); out['n2025_new']=len(new)
# combined: share of all 2025 Light requests that are either in backlog trechos or within 150 m of them
inb=f.u.isin(B0.index).sum(); out['share_backlog']=float(inb/len(f)); out['share_backlog_plus150']=float((inb+prev[150]*len(new))/len(f))
print(out['share_backlog'],out['share_backlog_plus150'])
# 3) top-500 frentes (r=150) at T + neighbours: coverage of 2025 requests within those frente areas (any trecho within 150 m of frente members)
t=greedy(B0,150); J=t.groupby('jan').n.sum().sort_values(ascending=False)
for K in [250,500,1000]:
    mem=t[t.jan.isin(J.index[:K])]
    tr2=BallTree(np.radians(mem[['lat','lon']].values),metric='haversine')
    c=tr2.query_radius(np.radians(f[['latitude_usada','longitude_usada']].values),150/R,count_only=True)
    inside_backlog=f.u.isin(mem.index)
    out[f'top{K}']=dict(only_backlog=float(inside_backlog.mean()),with_neighbors=float((c>0).mean()),trechos=len(mem))
    print(K,out[f'top{K}'])
json.dump(out,open('n3.json','w'))
