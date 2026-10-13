"""
Ranking "Onde podar agora" · J14 — Nota como chance
Tipo: principal

O que faz:
    Curva logística da nota para chance de árvore caída e de novo pedido na fiação (8
    datas).

Lê:
    df.pkl, pri_roll.pkl
Grava:
    ifnot.pkl
Usado em:
    Página: "Se não podar".
Script original da análise: light/ifnot.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np, pickle
O=pickle.load(open('pri_roll.pkl','rb'))
L=lambda v,cap: np.clip(np.log1p(v)/np.log1p(cap),0,1)
w=np.array([25,15,40,10,10])
def sc(g): return np.stack([L(g.risco+g.queda12,12),L(g.com,8),L(g.light,12),np.clip((g.prob-0.07)/0.48,0,1),np.clip(g.esp/365,0,1)],1)@w
rows=[]
for T,g in O.items():
    a=g.active; s=sc(g)
    rows.append(pd.DataFrame({'T':T,'s':s[a.values],'q':(g.y_queda[a]>0).values,'nq':g.y_queda[a].values,'l':(g.y_light[a]>0).values,'r':(g.y_rq[a]>0).values}))
B=pd.concat(rows)
B['b10']=(B.s//10).clip(0,9)
t=B.groupby('b10').agg(n=('s','size'),queda=('q','mean'),light=('l','mean'),risco=('r','mean'),quedas_media=('nq','mean'))
t['n']=(t.n/len(O)).round(); print(t.round(3))
from sklearn.linear_model import LogisticRegression
cal={}
for y in ['q','l','r']:
    m=LogisticRegression().fit(B[['s']].values/100,B[y].values)
    xs=np.arange(0,101,10); p=m.predict_proba(xs[:,None]/100)[:,1]; cal[y]=(float(m.intercept_[0]),float(m.coef_[0][0]))
    print(y,'logit',np.round(cal[y],3),'pred',np.round(p,3))
pickle.dump({'cal':cal,'bins':t},open('ifnot.pkl','wb'))
# share of falls in rainy season and time profile
A=pd.read_pickle('df.pkl'); A['ini']=pd.to_datetime(A.data_inicio)
q=A[A.subtipo.eq('Retirada de árvore caída')]
print('quedas dez-abr',round(q.ini.dt.month.isin([12,1,2,3,4]).mean(),3),'por mês',q.groupby(q.ini.dt.month).size().round().to_dict())
