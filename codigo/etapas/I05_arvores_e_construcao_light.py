"""
Frentes de desligamento · I05 — Árvores, construção e pedidos da Light por setor
Tipo: principal

O que faz:
    Pedidos da Light por 1.000 habitantes conforme cobertura de árvores e área construída do
    setor.

Lê:
    P.pkl, setor censitário (dados_entrada)
Grava:
    n2.json
Usado em:
    Página Light.
Script original da análise: light/n2.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np, json
S=pd.read_csv(SETOR)
P=pd.read_pickle('P.pkl'); P=P[P.cd_setor.notna()]
g=P.groupby(P.cd_setor.astype('int64')).agg(poda=('id_chamado','size'),light=('pend','sum'))
S=S.join(g,on='cd_setor').fillna({'poda':0,'light':0})
S['area']=S.area_km2.clip(lower=1e-3)
T=S[(S.total_de_p>50)].copy()
T['arv_q']=pd.qcut(T.arvore_urbana.rank(method='first'),5,labels=['1 (menos árvore)','2','3','4','5 (mais árvore)'])
T['con_q']=pd.qcut(T.construido.rank(method='first'),5,labels=['1','2','3','4','5'])
def summ(gb): 
    x=T.groupby(gb,observed=True).agg(setores=('cd_setor','size'),poda=('poda','sum'),light=('light','sum'),area=('area','sum'),popn=('total_de_p','sum'))
    x['light_km2']=x.light/x.area; x['light_por_mil_hab']=x.light/x.popn*1000; x['share']=x.light/x.poda; return x
a=summ('arv_q'); print(a.round(3))
# among denser built areas only
print(T.groupby(['con_q','arv_q'],observed=True).apply(lambda x: x.light.sum()/x.total_de_p.sum()*1000).unstack().round(2))
# Poisson model light ~ log pop + arvore + construido
from sklearn.linear_model import PoissonRegressor
X=np.c_[T.arvore_urbana,T.construido,np.log(T.total_de_p),np.log(T.area)]
mu=X.mean(0); sd=X.std(0)
m=PoissonRegressor(alpha=1e-4,max_iter=1000).fit((X-mu)/sd,T.light)
print(dict(zip(['arv','constr','logpop','logarea'],(m.coef_/sd).round(3))))
# effect: multiplicative per +0.1 arvore_urbana
print('x per +0.10 arvore urbana',np.exp(m.coef_[0]/sd[0]*0.1))
json.dump(dict(q=a.reset_index().astype({'arv_q':str}).to_dict('records'),eff=float(np.exp(m.coef_[0]/sd[0]*0.1))),open('n2.json','w'))
