"""
Ranking "Onde podar agora" · J10 — Modelo de aprendizado de máquina no lugar da soma
Tipo: teste descartado

O que faz:
    Gradient boosting no nível do CEP. Ganhou pouco e de forma instável.

Lê:
    código de J08_avaliar_sinais.py
Grava:
    nada (só imprime resultados)
Usado em:
    Comparação.
Script original da análise: light/pri_gbm.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _comum import *   # caminhos das pastas e arquivos; passa a trabalhar na pasta trabalho/

import pandas as pd, numpy as np, pickle
from sklearn.ensemble import HistGradientBoostingClassifier
exec(open(etapa('pri_eval.py')).read().split("rows=[]")[0])
KS=(200,500,1000)
F=['risco','queda12','com','light','light2y','prob','esp','light150','queda300','qcell','semprev','arv','risco_u','com_u','light_u']
def fit(Ts,y):
    X=pd.concat([O[T][O[T].active][F] for T in Ts]); yy=pd.concat([(O[T][O[T].active][y]>0).astype(int) for T in Ts])
    return HistGradientBoostingClassifier(max_iter=300,learning_rate=0.04,max_leaf_nodes=15,min_samples_leaf=80,l2_regularization=1.0,random_state=0).fit(X,yy)
for trainTs,tests in [(['2024-07-01'],['2025-01-01','2025-07-01']),(['2024-07-01','2025-01-01'],['2025-07-01'])]:
    M={y:fit(trainTs,y) for y in Y}
    for T in tests:
        g=O[T]; ranks=[]
        out={}
        for y in Y:
            p=M[y].predict_proba(g[F])[:,1]; ranks.append(pd.Series(p).rank(pct=True).values)
            e=ev(g,p,KS); out[y]=round(e[f'{y}@500'],3)
        comb=np.mean(ranks,0); e=ev(g,comb,KS); e0=ev(g,score(C[T],base),KS)
        print('treino',trainTs,'teste',T,'| GBM combinado obj',round(e['obj'],3),'| atual',round(e0['obj'],3),'| GBM por desfecho @500',out,
              '| atual @500',{y:round(e0[f'{y}@500'],3) for y in Y},'| quedas_cap@1000 GBM',round(e['quedas_cap@1000'],3),'atual',round(e0['quedas_cap@1000'],3))
